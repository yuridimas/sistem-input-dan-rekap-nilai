"""Business logic for user management.

Aturan pengelolaan pengguna untuk router users.

Service menerjemahkan konflik email; repository menangani persistence.
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories import user as user_repo
from app.schemas.user import UserCreate, UserUpdate
from app.services.auth import hash_password


async def create_user(db: AsyncSession, payload: UserCreate) -> User:
    """Cegah email ganda sebelum membuat data pengguna.

    Commit DB.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        payload: Data masukan yang sudah melewati validasi schema
            endpoint.

    Raises:
        HTTPException: 409 untuk identitas duplikat.
    """
    existing = await user_repo.get_by_email(db, payload.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email sudah terdaftar",
        )
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        is_active=True,
    )
    try:
        return await user_repo.add(db, user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email sudah terdaftar",
        )


async def get_user(db: AsyncSession, user_id: uuid.UUID) -> User:
    """Pastikan data pengguna ada sebelum proses lanjutan.

    Hanya membaca DB.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        user_id: Identitas akun yang dicari atau dikelola.

    Raises:
        HTTPException: 404 jika absen.
    """
    user = await user_repo.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pengguna tidak ditemukan",
        )
    return user


async def list_users(
    db: AsyncSession,
    role: str | None = None,
    is_active: bool | None = None,
) -> list[User]:
    """Sediakan daftar pengguna untuk pengelolaan router terkait.

    Hanya membaca DB dengan filter repository.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        role: Role akun atau filter role yang dipakai operasi.
        is_active: Filter status akun; None menyertakan kedua status.

    Returns:
        Daftar bisa kosong.
    """
    return await user_repo.list_users(db, role=role, is_active=is_active)


async def update_user(db: AsyncSession, user_id: uuid.UUID, payload: UserUpdate) -> User:
    """Terapkan perubahan parsial pengguna sesuai field yang dikirim.

    Commit DB.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        user_id: Identitas akun yang dicari atau dikelola.
        payload: Data masukan yang sudah melewati validasi schema
            endpoint.

    Raises:
        HTTPException: 404 jika absen atau 409 identitas duplikat.
    """
    user = await get_user(db, user_id)

    if payload.email is not None and payload.email != user.email:
        existing = await user_repo.get_by_email(db, payload.email)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email sudah terdaftar",
            )
        user.email = payload.email

    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.password is not None:
        user.password_hash = hash_password(payload.password)

    try:
        return await user_repo.save(db, user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email sudah terdaftar",
        )


async def deactivate_user(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Nonaktifkan akun tanpa menghapus relasi historisnya.

    Commit DB.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        user_id: Identitas akun yang dicari atau dikelola.

    Raises:
        HTTPException: 404 jika akun tidak ditemukan.
    """
    user = await get_user(db, user_id)
    user.is_active = False
    await user_repo.save(db, user)
