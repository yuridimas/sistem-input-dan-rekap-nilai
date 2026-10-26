"""Persistence roster dalam transaksi milik service.

Database access for enrollments; the calling service owns the
transaction.

Query dan persistence roster mahasiswa bagi service terkait.

Commit/rollback dimiliki service; error database diteruskan kecuali
disebutkan.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enrollment import Enrollment
from app.models.student import Student


async def get_by_id(db: AsyncSession, enrollment_id: uuid.UUID) -> Enrollment | None:
    """Cari keikutsertaan mahasiswa tanpa pemeriksaan akses.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        enrollment_id: UUID keikutsertaan mahasiswa pada satu kelas.
    """
    result = await db.execute(
        select(Enrollment).where(Enrollment.id == enrollment_id)
    )
    return result.scalar_one_or_none()


async def get_by_class_and_student(
    db: AsyncSession,
    class_id: uuid.UUID,
    student_id: uuid.UUID,
) -> Enrollment | None:
    """Periksa keunikan mahasiswa per kelas; None jika belum terdaftar.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        class_id: UUID kelas yang menjadi cakupan operasi.
        student_id: UUID profil mahasiswa, bukan UUID enrollment.
    """
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
    """Gabungkan roster dan profil dalam urutan NIM.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        class_id: UUID kelas yang menjadi cakupan operasi.
    """
    result = await db.execute(
        select(Enrollment, Student)
        .join(Student, Student.id == Enrollment.student_id)
        .where(Enrollment.class_id == class_id)
        .order_by(Student.nim.asc())
    )
    return list(result.all())


async def add(db: AsyncSession, enrollment: Enrollment) -> Enrollment:
    """Flush enrollment agar ID tersedia tanpa melepas lock kelas.

    Mutasi DB tanpa commit.

    Error constraint diteruskan.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        enrollment: Objek keikutsertaan mahasiswa yang dilacak session.
    """
    db.add(enrollment)
    await db.flush()
    return enrollment


async def delete(db: AsyncSession, enrollment: Enrollment) -> None:
    """Flush penghapusan roster dalam transaksi service.

    Mutasi DB tanpa commit.

    Error constraint diteruskan.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        enrollment: Objek keikutsertaan mahasiswa yang dilacak session.
    """
    await db.delete(enrollment)
    await db.flush()
