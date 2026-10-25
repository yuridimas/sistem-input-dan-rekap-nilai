"""Business logic for student management."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student
from app.repositories import student as student_repo
from app.schemas.student import StudentCreate, StudentUpdate


async def create_student(db: AsyncSession, payload: StudentCreate) -> Student:
    existing = await student_repo.get_by_nim(db, payload.nim)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="NIM sudah terdaftar",
        )
    student = Student(
        nim=payload.nim,
        full_name=payload.full_name,
        email=payload.email,
    )
    try:
        return await student_repo.add(db, student)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="NIM sudah terdaftar",
        )


async def list_students(db: AsyncSession) -> list[Student]:
    return await student_repo.list_students(db)


async def get_student(db: AsyncSession, student_id: uuid.UUID) -> Student:
    student = await student_repo.get_by_id(db, student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mahasiswa tidak ditemukan",
        )
    return student


async def update_student(
    db: AsyncSession,
    student_id: uuid.UUID,
    payload: StudentUpdate,
) -> Student:
    student = await get_student(db, student_id)

    if payload.nim is not None and payload.nim != student.nim:
        existing = await student_repo.get_by_nim(db, payload.nim)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="NIM sudah terdaftar",
            )
        student.nim = payload.nim

    if payload.full_name is not None:
        student.full_name = payload.full_name
    if "email" in payload.model_fields_set:
        student.email = payload.email

    try:
        return await student_repo.save(db, student)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="NIM sudah terdaftar",
        )


async def delete_student(db: AsyncSession, student_id: uuid.UUID) -> None:
    student = await get_student(db, student_id)
    try:
        await student_repo.delete(db, student)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Mahasiswa masih terdaftar di kelas dan tidak dapat dihapus",
        )
