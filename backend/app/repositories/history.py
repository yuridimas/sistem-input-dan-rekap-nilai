"""Batch queries for released history within the caller's lecturer scope."""

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
