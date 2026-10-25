"""Database access for classes."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.class_ import Class
from app.models.enrollment import Enrollment
from app.models.grade import Grade, GradeStatus


async def get_by_id(db: AsyncSession, class_id: uuid.UUID) -> Class | None:
    result = await db.execute(select(Class).where(Class.id == class_id))
    return result.scalar_one_or_none()


async def get_by_unique(
    db: AsyncSession,
    course_id: uuid.UUID,
    section: str,
    academic_year: str,
    exclude_id: uuid.UUID | None = None,
) -> Class | None:
    stmt = select(Class).where(
        Class.course_id == course_id,
        Class.section == section,
        Class.academic_year == academic_year,
    )
    if exclude_id is not None:
        stmt = stmt.where(Class.id != exclude_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_classes(
    db: AsyncSession,
    lecturer_id: uuid.UUID | None = None,
) -> list[Class]:
    stmt = select(Class).order_by(Class.created_at.desc())
    if lecturer_id is not None:
        stmt = stmt.where(Class.lecturer_id == lecturer_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def add(db: AsyncSession, class_: Class) -> Class:
    db.add(class_)
    await db.commit()
    await db.refresh(class_)
    return class_


async def save(db: AsyncSession, class_: Class) -> Class:
    await db.commit()
    await db.refresh(class_)
    return class_


async def delete(db: AsyncSession, class_: Class) -> None:
    await db.delete(class_)
    await db.commit()


async def finalized_class_ids(db: AsyncSession, class_ids: list[uuid.UUID]) -> set[uuid.UUID]:
    if not class_ids:
        return set()
    result = await db.scalars(select(Enrollment.class_id).join(
        Grade, Grade.enrollment_id == Enrollment.id,
    ).where(Enrollment.class_id.in_(class_ids), Grade.status == GradeStatus.FINALIZED).distinct())
    return set(result)
