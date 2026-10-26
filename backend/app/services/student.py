"""Business logic for student management.

Aturan pengelolaan mahasiswa untuk router students.

Service menerjemahkan konflik NIM; repository menangani persistence.
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student
from app.repositories import student as student_repo
from app.schemas.student import StudentCreate, StudentUpdate


async def create_student(db: AsyncSession, payload: StudentCreate) -> Student:
    """Cegah NIM ganda sebelum membuat data mahasiswa.

    Commit DB.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        payload: Data masukan yang sudah melewati validasi schema
            endpoint.

    Raises:
        HTTPException: 409 untuk identitas duplikat.
    """
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
    """Sediakan daftar mahasiswa untuk pengelolaan router terkait.

    Hanya membaca DB dengan filter repository.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.

    Returns:
        Daftar bisa kosong.
    """
    return await student_repo.list_students(db)


async def get_student(db: AsyncSession, student_id: uuid.UUID) -> Student:
    """Pastikan data mahasiswa ada sebelum proses lanjutan.

    Hanya membaca DB.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        student_id: UUID profil mahasiswa, bukan UUID enrollment.

    Raises:
        HTTPException: 404 jika absen.
    """
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
    """Terapkan perubahan parsial mahasiswa sesuai field yang dikirim.

    Commit DB.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        student_id: UUID profil mahasiswa, bukan UUID enrollment.
        payload: Data masukan yang sudah melewati validasi schema
            endpoint.

    Raises:
        HTTPException: 404 jika absen atau 409 identitas duplikat.
    """
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
    # Null yang dikirim sengaja menghapus email; field absen mempertahankan nilai lama.
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
    """Pertahankan integritas roster ketika menghapus mahasiswa.

    Commit DB.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        student_id: UUID profil mahasiswa, bukan UUID enrollment.

    Raises:
        HTTPException: 404 jika absen atau 409 jika masih terdaftar.
    """
    student = await get_student(db, student_id)
    try:
        await student_repo.delete(db, student)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Mahasiswa masih terdaftar di kelas dan tidak dapat dihapus",
        )
