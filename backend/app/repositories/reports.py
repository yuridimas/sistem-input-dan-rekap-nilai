"""Batch report queries including students without a finalized grade.

Query dan persistence data laporan bagi service terkait.

Commit/rollback dimiliki service; error database diteruskan kecuali
disebutkan.
"""

import uuid

from sqlalchemy import Select, and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enrollment import Enrollment
from app.models.grade import Grade
from app.models.ranking import Ranking
from app.models.student import Student


def _rows() -> Select:
    """Susun SELECT roster dengan nilai dan ranking opsional."""
    return (select(Enrollment, Student, Grade, Ranking.rank).select_from(Enrollment)
            .join(Student, Student.id == Enrollment.student_id)
            .outerjoin(Grade, Grade.enrollment_id == Enrollment.id)
            .outerjoin(Ranking, and_(Ranking.enrollment_id == Enrollment.id, Ranking.class_id == Enrollment.class_id)))


async def get_student(db: AsyncSession, enrollment_id: uuid.UUID) -> tuple[Enrollment, Student, Grade | None, int | None] | None:
    """Baca konteks enrollment untuk divalidasi oleh service laporan.

    Grade/rank bisa None, tanpa otorisasi.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        enrollment_id: UUID keikutsertaan mahasiswa pada satu kelas.

    Returns:
        Konteks enrollment dan profil beserta nilai/ranking opsional;
        None jika enrollment absen.
    """
    return (await db.execute(_rows().where(Enrollment.id == enrollment_id))).one_or_none()


async def list_class(db: AsyncSession, class_id: uuid.UUID) -> list[tuple[Enrollment, Student, Grade | None, int | None]]:
    """Muat seluruh roster untuk validasi kelayakan export.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        class_id: UUID kelas yang menjadi cakupan operasi.

    Returns:
        Seluruh baris roster terurut NIM/nama/ID; nilai dan ranking
        boleh None, daftar bisa kosong.
    """
    result = await db.execute(_rows().where(Enrollment.class_id == class_id).order_by(Student.nim, Student.full_name, Enrollment.id))
    return list(result.all())
