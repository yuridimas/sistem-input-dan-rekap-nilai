"""Database access for users.

Akses persistence pengguna untuk service terkait; otorisasi berada di
service/router.

Operasi add/save/delete di modul ini melakukan commit; pembacaan tidak
mengubah data.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """Cari pengguna dari UUID tanpa otorisasi.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        user_id: Identitas akun yang dicari atau dikelola.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    """Cari identitas email tanpa memverifikasi password.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        email: Email akun yang dipakai untuk pencarian identitas.
    """
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def list_users(
    db: AsyncSession,
    role: str | None = None,
    is_active: bool | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[User]:
    """Baca pengguna terbaru dengan filter dan pagination.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        role: Role akun atau filter role yang dipakai operasi.
        is_active: Filter status akun; None menyertakan kedua status.
        limit: Jumlah maksimum pengguna yang diambil; default 100.
        offset: Jumlah baris pengguna yang dilewati; default nol.
    """
    stmt = select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
    if role is not None:
        stmt = stmt.where(User.role == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def add(db: AsyncSession, user: User) -> User:
    """Simpan pengguna baru dan muat default database.

    Commit/refresh DB; error constraint diteruskan ke service.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        user: Objek akun untuk pemeriksaan akses atau persistence sesuai
            operasi.
    """
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def save(db: AsyncSession, user: User) -> User:
    """Simpan perubahan pengguna yang sudah dilacak session.

    Commit/refresh DB; error constraint diteruskan ke service.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        user: Objek akun untuk pemeriksaan akses atau persistence sesuai
            operasi.
    """
    await db.commit()
    await db.refresh(user)
    return user
