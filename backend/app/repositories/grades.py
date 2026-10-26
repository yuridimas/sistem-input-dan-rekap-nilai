"""Grade persistence; the calling service owns commit and rollback.

Query dan persistence nilai akhir bagi service terkait.

Commit/rollback dimiliki service; error database diteruskan kecuali
disebutkan.
"""

import uuid
from decimal import Decimal

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enrollment import Enrollment
from app.models.grade import Grade, GradeStatus


async def has_finalized_class(db: AsyncSession, class_id: uuid.UUID) -> bool:
    """Cari minimal satu nilai final sebagai batas perubahan kelas.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        class_id: UUID kelas yang menjadi cakupan operasi.
    """
    return bool(await db.scalar(select(exists().where(
        Grade.enrollment_id == Enrollment.id,
        Enrollment.class_id == class_id,
        Grade.status == GradeStatus.FINALIZED,
    ))))


async def get_by_enrollment(db: AsyncSession, enrollment_id: uuid.UUID) -> Grade | None:
    """Muat ulang total/status enrollment; None jika draft belum dibuat.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        enrollment_id: UUID keikutsertaan mahasiswa pada satu kelas.
    """
    return (await db.execute(
        select(Grade).where(Grade.enrollment_id == enrollment_id).execution_options(populate_existing=True)
    )).scalar_one_or_none()


async def list_by_class(db: AsyncSession, class_id: uuid.UUID) -> list[Grade]:
    """Muat ulang nilai seluruh enrollment kelas secara batch.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        class_id: UUID kelas yang menjadi cakupan operasi.
    """
    result = await db.execute(
        select(Grade).join(Enrollment, Enrollment.id == Grade.enrollment_id)
        .where(Enrollment.class_id == class_id).execution_options(populate_existing=True)
    )
    return list(result.scalars())


def add_draft(db: AsyncSession, enrollment_id: uuid.UUID, final_score: Decimal) -> Grade:
    """Daftarkan total draft yang telah dihitung service.

    Mengubah session tanpa flush/commit.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        enrollment_id: UUID keikutsertaan mahasiswa pada satu kelas.
        final_score: Total Decimal yang telah dihitung service pada
            skala seratus.
    """
    grade = Grade(enrollment_id=enrollment_id, final_score=final_score)
    db.add(grade)
    return grade
