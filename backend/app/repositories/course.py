"""Database access for courses."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course


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
        stmt = stmt.where(Course.created_by == created_by)
    result = await db.execute(stmt)
    return list(result.scalars().all())


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
