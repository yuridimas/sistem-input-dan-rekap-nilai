"""Query history final sesuai cakupan dosen.

Batch queries for released history within the caller's lecturer scope.

Query dan persistence riwayat final bagi service terkait.

Commit/rollback dimiliki service; error database diteruskan kecuali
disebutkan.
"""

import uuid
from decimal import Decimal

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.class_ import Class
from app.models.component import Component
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.grade import Grade, GradeStatus
from app.models.ranking import Ranking
from app.models.score import Score


async def list_finalized(
    db: AsyncSession, student_id: uuid.UUID, lecturer_id: uuid.UUID | None,
) -> list[tuple[Grade, Enrollment, Course, Class, int | None]]:
    """Baca riwayat final terbaru sesuai cakupan dosen.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        student_id: UUID profil mahasiswa, bukan UUID enrollment.
        lecturer_id: UUID dosen penugasan; None membuka cakupan seluruh
            dosen.

    Returns:
        Daftar baris final terurut rilis; ranking bisa None dan daftar
        bisa kosong.
    """
    stmt = (
        select(Grade, Enrollment, Course, Class, Ranking.rank).select_from(Grade)
        .join(Enrollment, Enrollment.id == Grade.enrollment_id)
        .join(Class, Class.id == Enrollment.class_id)
        .join(Course, Course.id == Class.course_id)
        .outerjoin(Ranking, and_(Ranking.enrollment_id == Enrollment.id, Ranking.class_id == Class.id))
        .where(Enrollment.student_id == student_id, Grade.status == GradeStatus.FINALIZED)
        .order_by(Grade.finalized_at.desc().nulls_last(), Enrollment.id.asc())
    )
    if lecturer_id is not None:
        stmt = stmt.where(Class.lecturer_id == lecturer_id)
    return list((await db.execute(stmt)).all())


async def list_components(
    db: AsyncSession, enrollment_ids: list[uuid.UUID],
) -> list[tuple[uuid.UUID, Component, Decimal | None]]:
    """Muat komponen/skor banyak enrollment dalam satu query.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        enrollment_ids: UUID enrollment yang dibaca secara batch; boleh
            kosong.

    Returns:
        Daftar pasangan enrollment/komponen dengan skor opsional; input
        kosong menghasilkan [].
    """
    if not enrollment_ids:
        return []
    result = await db.execute(
        select(Enrollment.id, Component, Score.score).select_from(Enrollment)
        .join(Component, Component.class_id == Enrollment.class_id)
        .outerjoin(Score, and_(Score.enrollment_id == Enrollment.id, Score.component_id == Component.id))
        .where(Enrollment.id.in_(enrollment_ids))
        .order_by(Enrollment.id, Component.order_index, Component.created_at, Component.id)
    )
    return list(result.all())
