"""Batch report queries including students without a finalized grade."""

import uuid

from sqlalchemy import Select, and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enrollment import Enrollment
from app.models.grade import Grade
from app.models.ranking import Ranking
from app.models.student import Student


def _rows() -> Select:
    return (select(Enrollment, Student, Grade, Ranking.rank).select_from(Enrollment)
            .join(Student, Student.id == Enrollment.student_id)
            .outerjoin(Grade, Grade.enrollment_id == Enrollment.id)
            .outerjoin(Ranking, and_(Ranking.enrollment_id == Enrollment.id, Ranking.class_id == Enrollment.class_id)))


async def get_student(db: AsyncSession, enrollment_id: uuid.UUID) -> tuple[Enrollment, Student, Grade | None, int | None] | None:
    return (await db.execute(_rows().where(Enrollment.id == enrollment_id))).one_or_none()


async def list_class(db: AsyncSession, class_id: uuid.UUID) -> list[tuple[Enrollment, Student, Grade | None, int | None]]:
    result = await db.execute(_rows().where(Enrollment.class_id == class_id).order_by(Student.nim, Student.full_name, Enrollment.id))
    return list(result.all())
