"""Batched dashboard reads; aggregate before joining courses and classes."""

import uuid

from sqlalchemy import RowMapping, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.class_ import Class
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.grade import Grade, GradeStatus


async def list_summary_rows(db: AsyncSession, lecturer_id: uuid.UUID | None) -> list[RowMapping]:
    counts = (
        select(
            Enrollment.class_id,
            func.count(Enrollment.id).label("student_count"),
            func.count(case((Grade.status == GradeStatus.FINALIZED, 1))).label("finalized_count"),
            func.max(case((Grade.status == GradeStatus.FINALIZED, Grade.finalized_at))).label("released_at"),
        )
        .outerjoin(Grade, Grade.enrollment_id == Enrollment.id)
        .group_by(Enrollment.class_id)
        .subquery()
    )
    statement = (
        select(
            Course.id.label("course_id"), Course.code, Course.name, Course.semester,
            Class.id.label("class_id"), Class.section, Class.academic_year,
            func.coalesce(counts.c.student_count, 0).label("student_count"),
            func.coalesce(counts.c.finalized_count, 0).label("finalized_count"),
            counts.c.released_at,
        )
        .select_from(Course)
        .outerjoin(Class, Class.course_id == Course.id)
        .outerjoin(counts, counts.c.class_id == Class.id)
        .order_by(Course.code, Course.id, Class.academic_year.desc(), Class.section, Class.id)
    )
    if lecturer_id is not None:
        statement = statement.where(Class.lecturer_id == lecturer_id)
    return list((await db.execute(statement)).mappings().all())
