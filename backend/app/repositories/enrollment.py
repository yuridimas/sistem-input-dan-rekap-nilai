"""Database access for enrollments; the calling service owns the transaction."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enrollment import Enrollment
from app.models.student import Student


async def get_by_id(db: AsyncSession, enrollment_id: uuid.UUID) -> Enrollment | None:
    result = await db.execute(
        select(Enrollment).where(Enrollment.id == enrollment_id)
    )
    return result.scalar_one_or_none()


async def get_by_class_and_student(
    db: AsyncSession,
    class_id: uuid.UUID,
    student_id: uuid.UUID,
) -> Enrollment | None:
    result = await db.execute(
        select(Enrollment).where(
            Enrollment.class_id == class_id,
            Enrollment.student_id == student_id,
        )
    )
    return result.scalar_one_or_none()


async def list_by_class(
    db: AsyncSession,
    class_id: uuid.UUID,
) -> list[tuple[Enrollment, Student]]:
    result = await db.execute(
        select(Enrollment, Student)
        .join(Student, Student.id == Enrollment.student_id)
        .where(Enrollment.class_id == class_id)
        .order_by(Student.nim.asc())
    )
    return list(result.all())


async def add(db: AsyncSession, enrollment: Enrollment) -> Enrollment:
    db.add(enrollment)
    await db.flush()
    return enrollment


async def delete(db: AsyncSession, enrollment: Enrollment) -> None:
    await db.delete(enrollment)
    await db.flush()
