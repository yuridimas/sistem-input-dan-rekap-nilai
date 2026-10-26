"""Class grade grids.

Adapter HTTP nilai, finalisasi, dan history yang didaftarkan app.main.

Dependency menetapkan identitas/role; aturan bisnis dan persistence
didelegasikan ke service.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User
from app.schemas.grades import ClassGradesRead, FinalizeRead, RankingRead
from app.schemas.history import HistoryRead
from app.services.grade import class_grades, finalize_class
from app.services.ranking import class_ranking
from app.services.history import student_history

router = APIRouter(tags=["grades"])


@router.get("/classes/{class_id}/grades", response_model=ClassGradesRead)
async def get_class_grades(
    class_id: uuid.UUID, db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("superadmin", "lecturer")),
) -> ClassGradesRead:
    """Sajikan snapshot grid nilai kelas yang diizinkan.

    \f

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        class_id: UUID kelas yang menjadi cakupan operasi.
        db: Session database; batas commit mengikuti operasi terkait.
        user: Objek akun untuk pemeriksaan akses atau persistence sesuai
            operasi.

    Returns:
        Snapshot komponen dan seluruh baris roster editor.
    """
    return await class_grades(db, class_id, user)


@router.post("/classes/{class_id}/finalize", response_model=FinalizeRead, status_code=202)
async def finalize_grades(
    class_id: uuid.UUID, db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("superadmin", "lecturer")),
) -> FinalizeRead:
    """Rilis nilai kelas dan laporkan jumlah task yang diantrekan.

    \f

    Angka notified hanya menghitung task yang diterima antrean, bukan
    email yang sampai.

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        class_id: UUID kelas yang menjadi cakupan operasi.
        db: Session database; batas commit mengikuti operasi terkait.
        user: Objek akun untuk pemeriksaan akses atau persistence sesuai
            operasi.

    Returns:
        Jumlah nilai final dan task yang diterima antrean.
    """
    return await finalize_class(db, class_id, user)


@router.get("/classes/{class_id}/ranking", response_model=list[RankingRead])
async def get_ranking(
    class_id: uuid.UUID, db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("superadmin", "lecturer")),
) -> list[RankingRead]:
    """Sajikan snapshot ranking final, bukan perhitungan ulang saat GET.

    \f

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        class_id: UUID kelas yang menjadi cakupan operasi.
        db: Session database; batas commit mengikuti operasi terkait.
        user: Objek akun untuk pemeriksaan akses atau persistence sesuai
            operasi.

    Returns:
        Daftar ranking tersimpan; kosong jika belum ada snapshot.
    """
    return await class_ranking(db, class_id, user)


@router.get("/students/{student_id}/history", response_model=list[HistoryRead])
async def get_student_history(
    student_id: uuid.UUID, db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("superadmin", "lecturer")),
) -> list[HistoryRead]:
    """Sajikan history final mahasiswa sesuai cakupan pengguna.

    \f

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        student_id: UUID profil mahasiswa, bukan UUID enrollment.
        db: Session database; batas commit mengikuti operasi terkait.
        user: Objek akun untuk pemeriksaan akses atau persistence sesuai
            operasi.

    Returns:
        Daftar hasil final yang terlihat; bisa kosong.
    """
    return await student_history(db, student_id, user)
