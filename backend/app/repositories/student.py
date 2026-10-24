"""Database access for students."""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student


async def get_by_id(db: AsyncSession, student_id: uuid.UUID) -> Student | None:
    result = await db.execute(select(Student).where(Student.id == student_id))
    return result.scalar_one_or_none()


async def get_by_nim(db: AsyncSession, nim: str) -> Student | None:
    result = await db.execute(select(Student).where(Student.nim == nim))
    return result.scalar_one_or_none()


async def list_students(db: AsyncSession) -> list[Student]:
    result = await db.execute(select(Student).order_by(Student.nim.asc()))
    return list(result.scalars().all())


async def add(db: AsyncSession, student: Student) -> Student:
    db.add(student)
    await db.commit()
    await db.refresh(student)
    return student


async def get_or_create_for_enrollment(db: AsyncSession, student: Student) -> Student:
    existing = await get_by_nim(db, student.nim)
    if existing is not None:
        return existing
    nim = student.nim
    try:
        # A conflicting NIM must not roll back the outer transaction's class lock.
        async with db.begin_nested():
            db.add(student)
            await db.flush()
    except IntegrityError:
        existing = await get_by_nim(db, nim)
        if existing is None:
            raise
        return existing
    return student


async def save(db: AsyncSession, student: Student) -> Student:
    await db.commit()
    await db.refresh(student)
    return student


async def delete(db: AsyncSession, student: Student) -> None:
    await db.delete(student)
    await db.commit()
