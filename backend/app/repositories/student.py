"""Database access for students.

Akses persistence mahasiswa untuk service terkait; otorisasi berada di
service/router.

Operasi add/save/delete di modul ini melakukan commit; pembacaan tidak
mengubah data.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student


async def get_by_id(db: AsyncSession, student_id: uuid.UUID) -> Student | None:
    """Cari mahasiswa dari UUID tanpa otorisasi.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        student_id: UUID profil mahasiswa, bukan UUID enrollment.
    """
    result = await db.execute(select(Student).where(Student.id == student_id))
    return result.scalar_one_or_none()


async def get_by_nim(db: AsyncSession, nim: str) -> Student | None:
    """Cari NIM unik untuk memakai ulang profil mahasiswa.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        nim: NIM unik yang dipakai untuk pencarian profil mahasiswa.
    """
    result = await db.execute(select(Student).where(Student.nim == nim))
    return result.scalar_one_or_none()


async def list_students(db: AsyncSession) -> list[Student]:
    """Baca profil mahasiswa dalam urutan NIM.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
    """
    result = await db.execute(select(Student).order_by(Student.nim.asc()))
    return list(result.scalars().all())


async def add(db: AsyncSession, student: Student) -> Student:
    """Simpan mahasiswa baru dan muat default database.

    Commit/refresh DB; error constraint diteruskan ke service.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        student: Objek profil mahasiswa yang dilacak session.
    """
    db.add(student)
    await db.commit()
    await db.refresh(student)
    return student


async def get_or_create_for_enrollment(db: AsyncSession, student: Student) -> Student:
    """Pakai ulang NIM atau insert profil melalui savepoint.

    Tidak commit.

    Flush/savepoint menjaga lock transaksi luar, error tak terpulihkan
    diteruskan.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        student: Objek profil mahasiswa yang dilacak session.
    """
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
    """Simpan perubahan mahasiswa yang sudah dilacak session.

    Commit/refresh DB; error constraint diteruskan ke service.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        student: Objek profil mahasiswa yang dilacak session.
    """
    await db.commit()
    await db.refresh(student)
    return student


async def delete(db: AsyncSession, student: Student) -> None:
    """Hapus mahasiswa dengan proteksi constraint relasi.

    Commit DB; IntegrityError diterjemahkan oleh service.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        student: Objek profil mahasiswa yang dilacak session.
    """
    await db.delete(student)
    await db.commit()
