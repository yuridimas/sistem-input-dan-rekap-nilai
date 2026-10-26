"""Seed helpers (idempotent).

Bootstrap akun superadmin dari konfigurasi saat startup main.

Session opsional memudahkan pengujian tanpa membuat koneksi tersendiri.
"""

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.user import User, UserRole


async def seed_superadmin(session: AsyncSession | None = None) -> User | None:
    """Buat akun awal jika konfigurasi tersedia dan email belum ada.

    Create the superadmin account from env if none exists (idempotent).

    Commit saat insert, tutup hanya session milik sendiri.

    Args:
        session: Session opsional; None membuat session yang ditutup
            sendiri.

    Returns:
        None jika konfigurasi kosong.
    """
    settings = get_settings()
    email = settings.superadmin_email
    password = settings.superadmin_password
    name = settings.superadmin_name

    if not email or not password:
        return None

    own_session = session is None
    if own_session:
        session = AsyncSessionLocal()

    try:
        result = await session.execute(select(User).where(User.email == email))
        existing = result.scalar_one_or_none()
        if existing is not None:
            return existing

        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user = User(
            email=email,
            password_hash=hashed,
            full_name=name,
            role=UserRole.SUPERADMIN,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    finally:
        if own_session:
            await session.close()