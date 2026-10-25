"""Database access for courses."""

import uuid

from sqlalchemy import exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course
from app.models.class_ import Class


async def get_by_id(db: AsyncSession, course_id: uuid.UUID) -> Course | None:
    result = await db.execute(select(Course).where(Course.id == course_id))
    return result.scalar_one_or_none()


async def get_by_code(db: AsyncSession, code: str) -> Course | None:
    result = await db.execute(select(Course).where(Course.code == code))
    return result.scalar_one_or_none()


async def list_courses(
    db: AsyncSession,
    created_by: uuid.UUID | None = None,
) -> list[Course]:
    stmt = select(Course).order_by(Course.created_at.desc())
    if created_by is not None:
        stmt = stmt.where(or_(Course.created_by == created_by, exists().where(
            Class.course_id == Course.id, Class.lecturer_id == created_by,
        )))
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def has_assigned_class(db: AsyncSession, course_id: uuid.UUID, lecturer_id: uuid.UUID) -> bool:
    return bool(await db.scalar(select(exists().where(
        Class.course_id == course_id, Class.lecturer_id == lecturer_id,
    ))))


async def add(db: AsyncSession, course: Course) -> Course:
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


async def save(db: AsyncSession, course: Course) -> Course:
    await db.commit()
    await db.refresh(course)
    return course


async def delete(db: AsyncSession, course: Course) -> None:
    await db.delete(course)
    await db.commit()
