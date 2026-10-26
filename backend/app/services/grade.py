"""Decimal grade calculation and roster response assembly.

Aturan nilai dan finalisasi yang dipakai router grades serta service
scores/components.

Repository menangani akses data; service ini menjaga konsistensi hasil
dan batas transaksi.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from fractions import Fraction

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.component import Component
from app.models.grade import GradeStatus
from app.models.user import User
from app.repositories import component as component_repo
from app.repositories import enrollment as enrollment_repo
from app.repositories import grades as grade_repo
from app.repositories import scores as score_repo
from app.repositories import ranking as ranking_repo
from app.repositories import notifications as notification_repo
from app.schemas.component import ComponentCreate, ComponentRead
from app.schemas.grades import ClassGradesRead, FinalizeRead, GradeRowRead
from app.schemas.student import StudentRead
from app.services.class_ import get_class
from app.services.component_rules import validate_configuration
from app.services.release_notifications import publish_grade_releases
from app.services.notifications import record_enqueue_result


def calculate_final_score(components: list[Component], scores: dict[uuid.UUID, Decimal]) -> Decimal:
    """Hitung nilai berbobot dengan pembulatan yang konsisten.

    Pembagian memakai pecahan eksak agar batas setengah sen tidak
    bergeser.

    Args:
        components: Komponen berbobot valid dengan max_score lebih besar
            dari nol.
        scores: Skor Decimal per UUID komponen; komponen absen
            berkontribusi nol.

    Returns:
        Total Decimal dua desimal yang dibulatkan half-up.
    """
    # Missing scores contribute zero; retain full class weights for partial drafts.
    # Normalize exactly so repeating divisions cannot move a half-cent below its boundary.
    total = sum((
        Fraction(scores.get(component.id, Decimal("0"))) * Fraction(component.weight) / Fraction(component.max_score)
        for component in components
    ), Fraction(0))
    # Pecahan eksak menjaga aturan half-up, termasuk ketika pembagian bobot berulang.
    cents = total * 100
    whole, remainder = divmod(cents.numerator, cents.denominator)
    if remainder * 2 >= cents.denominator:
        whole += 1
    return Decimal(whole).scaleb(-2)


async def ensure_components_mutable(db: AsyncSession, class_id: uuid.UUID) -> None:
    """Tolak perubahan komponen pada kelas dengan nilai final.

    Membaca status tanpa commit.

    Pemanggil bertanggung jawab atas lock kelas.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        class_id: UUID kelas yang menjadi cakupan operasi.

    Raises:
        HTTPException: 409 jika ada nilai final.
    """
    if await grade_repo.has_finalized_class(db, class_id):
        raise HTTPException(409, "Komponen kelas dengan nilai final tidak dapat diubah")


async def validate_score_compatibility(
    db: AsyncSession, class_id: uuid.UUID, maximums: dict[uuid.UUID, Decimal],
) -> None:
    """Jaga kompatibilitas konfigurasi terhadap skor tersimpan.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        class_id: UUID kelas yang menjadi cakupan operasi.
        maximums: Maksimum komponen tujuan; komponen berskor tidak boleh
            hilang.

    Raises:
        HTTPException: 409 untuk penghapusan, 422 untuk maksimum terlalu
            kecil.
    """
    for score in await score_repo.list_by_class(db, class_id):
        if score.component_id not in maximums:
            raise HTTPException(409, "Komponen yang sudah memiliki nilai tidak dapat dihapus")
        if score.score > maximums[score.component_id]:
            raise HTTPException(422, "Nilai maksimum tidak boleh lebih kecil dari nilai yang tersimpan")


async def recalculate_class_drafts(db: AsyncSession, class_id: uuid.UUID) -> None:
    """Hitung ulang total draft setelah konfigurasi berubah.

    Nilai yang sudah final tidak dihitung ulang.

    Mengubah objek Grade dalam session; commit tetap dilakukan
    pemanggil.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        class_id: UUID kelas yang menjadi cakupan operasi.
    """
    components = await component_repo.list_by_class(db, class_id)
    scores: dict[uuid.UUID, dict[uuid.UUID, Decimal]] = {}
    for score in await score_repo.list_by_class(db, class_id):
        scores.setdefault(score.enrollment_id, {})[score.component_id] = score.score
    for grade in await grade_repo.list_by_class(db, class_id):
        if grade.status == GradeStatus.DRAFT:
            grade.final_score = calculate_final_score(components, scores.get(grade.enrollment_id, {}))


async def class_grades(db: AsyncSession, class_id: uuid.UUID, user: User) -> ClassGradesRead:
    """Susun grid lengkap termasuk roster yang belum memiliki nilai.

    Hanya membaca database.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        class_id: UUID kelas yang menjadi cakupan operasi.
        user: Objek akun untuk pemeriksaan akses atau persistence sesuai
            operasi.

    Returns:
        ClassGradesRead. Skor kosong berupa dict kosong.

    Raises:
        HTTPException: 403/404 dari pemeriksaan akses kelas.
    """
    await get_class(db, class_id, user)
    components = await component_repo.list_by_class(db, class_id)
    roster = await enrollment_repo.list_by_class(db, class_id)
    grades = {grade.enrollment_id: grade for grade in await grade_repo.list_by_class(db, class_id)}
    score_maps: dict[uuid.UUID, dict[uuid.UUID, Decimal]] = {}
    for score in await score_repo.list_by_class(db, class_id):
        score_maps.setdefault(score.enrollment_id, {})[score.component_id] = score.score
    rows = []
    for enrollment, student in roster:
        grade = grades.get(enrollment.id)
        rows.append(GradeRowRead(
            enrollment_id=enrollment.id, student=StudentRead.model_validate(student),
            scores=score_maps.get(enrollment.id, {}), final_score=grade.final_score if grade else None,
            status=grade.status if grade else GradeStatus.DRAFT,
        ))
    return ClassGradesRead(
        class_id=class_id, components=[ComponentRead.model_validate(row) for row in components], grades=rows,
    )


async def finalize_class(db: AsyncSession, class_id: uuid.UUID, user: User) -> FinalizeRead:
    """Rilis roster, ranking, dan catatan notifikasi secara atomik.

    Lock/commit DB lalu enqueue; HTTPException 403/404, 409 konflik, 422
    data belum valid.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        class_id: UUID kelas yang menjadi cakupan operasi.
        user: Objek akun untuk pemeriksaan akses atau persistence sesuai
            operasi.

    Returns:
        FinalizeRead berisi jumlah final dan enqueue.
    """
    # Lock yang sama dipakai perubahan komponen, skor, dan roster untuk menutup race finalisasi.
    await component_repo.lock_class(db, class_id)
    await get_class(db, class_id, user)
    if await grade_repo.has_finalized_class(db, class_id):
        raise HTTPException(409, "Nilai kelas sudah difinalisasi")
    components = await component_repo.list_by_class(db, class_id)
    validate_configuration([ComponentCreate.model_validate(row, from_attributes=True) for row in components])
    roster = await enrollment_repo.list_by_class(db, class_id)
    if not roster:
        raise HTTPException(422, "Kelas belum memiliki mahasiswa")
    score_maps: dict[uuid.UUID, dict[uuid.UUID, Decimal]] = {}
    maximums = {component.id: component.max_score for component in components}
    for score in await score_repo.list_by_class(db, class_id):
        if score.component_id not in maximums or not score.score.is_finite() or not 0 <= score.score <= maximums[score.component_id]:
            raise HTTPException(422, "Nilai tersimpan tidak sesuai komponen kelas")
        score_maps.setdefault(score.enrollment_id, {})[score.component_id] = score.score
    # Skor nol tetap lengkap; hanya komponen tanpa entri yang menghalangi publikasi.
    missing = [
        {"student_nim": student.nim, "component_name": component.name}
        for enrollment, student in roster for component in components
        if component.id not in score_maps.get(enrollment.id, {})
    ]
    if missing:
        raise HTTPException(422, {"message": "Nilai komponen belum lengkap", "missing": missing})
    grades = {grade.enrollment_id: grade for grade in await grade_repo.list_by_class(db, class_id)}
    finalized_at = datetime.now(timezone.utc)
    try:
        for enrollment, _student in roster:
            final_score = calculate_final_score(components, score_maps[enrollment.id])
            grade = grades.get(enrollment.id)
            if grade is None:
                grade = grade_repo.add_draft(db, enrollment.id, final_score)
                grades[enrollment.id] = grade
            grade.final_score = final_score
            grade.status = GradeStatus.FINALIZED
            grade.finalized_at = finalized_at
            grade.finalized_by = user.id
        await db.flush()
        await ranking_repo.create_for_class(db, class_id, finalized_at)
        grade_ids = [grades[enrollment.id].id for enrollment, _student in roster]
        dispatch_tokens = notification_repo.add_releases(db, [(grades[enrollment.id].id, student.email) for enrollment, student in roster])
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Finalisasi gagal karena data kelas telah berubah")
    # Task baru diterbitkan setelah commit agar worker tidak membaca hasil yang belum tersimpan.
    # Jumlah ini menyatakan enqueue berhasil, bukan email yang sudah sampai.
    notified = await publish_grade_releases(grade_ids)
    await record_enqueue_result(db, grade_ids, notified, dispatch_tokens)
    return FinalizeRead(finalized_count=len(grade_ids), notified=notified)
