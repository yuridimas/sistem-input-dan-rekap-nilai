"""Database access for courses.

Akses persistence mata kuliah untuk service terkait; otorisasi berada di
service/router.

Operasi add/save/delete di modul ini melakukan commit; pembacaan tidak
mengubah data.
"""

import uuid

from sqlalchemy import exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course
from app.models.class_ import Class


async def get_by_id(db: AsyncSession, course_id: uuid.UUID) -> Course | None:
    """Cari mata kuliah dari UUID tanpa otorisasi.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        course_id: UUID mata kuliah yang menjadi sasaran operasi.
    """
    result = await db.execute(select(Course).where(Course.id == course_id))
    return result.scalar_one_or_none()


async def get_by_code(db: AsyncSession, code: str) -> Course | None:
    """Cari kode unik untuk validasi konflik; None jika belum terpakai.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        code: Kode unik mata kuliah yang dicari.
    """
    result = await db.execute(select(Course).where(Course.code == code))
    return result.scalar_one_or_none()


async def list_courses(
    db: AsyncSession,
    created_by: uuid.UUID | None = None,
) -> list[Course]:
    """Baca mata kuliah pencipta atau kelas penugasan dosen.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        created_by: UUID pencipta atau dosen penugasan; None meniadakan
            filter.
    """
    stmt = select(Course).order_by(Course.created_at.desc())
    if created_by is not None:
        stmt = stmt.where(or_(Course.created_by == created_by, exists().where(
            Class.course_id == Course.id, Class.lecturer_id == created_by,
        )))
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def has_assigned_class(db: AsyncSession, course_id: uuid.UUID, lecturer_id: uuid.UUID) -> bool:
    """Periksa keberadaan kelas penugasan dosen.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        course_id: UUID mata kuliah yang menjadi sasaran operasi.
        lecturer_id: UUID dosen yang harus memiliki kelas pada mata
            kuliah tujuan.
    """
    return bool(await db.scalar(select(exists().where(
        Class.course_id == course_id, Class.lecturer_id == lecturer_id,
    ))))


async def add(db: AsyncSession, course: Course) -> Course:
    """Simpan mata kuliah baru dan muat default database.

    Commit/refresh DB; error constraint diteruskan ke service.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        course: Objek mata kuliah yang dilacak session.
    """
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


async def save(db: AsyncSession, course: Course) -> Course:
    """Simpan perubahan mata kuliah yang sudah dilacak session.

    Commit/refresh DB; error constraint diteruskan ke service.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        course: Objek mata kuliah yang dilacak session.
    """
    await db.commit()
    await db.refresh(course)
    return course


async def delete(db: AsyncSession, course: Course) -> None:
    """Hapus mata kuliah dengan proteksi constraint relasi.

    Commit DB; IntegrityError diterjemahkan oleh service.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        course: Objek mata kuliah yang dilacak session.
    """
    await db.delete(course)
    await db.commit()
