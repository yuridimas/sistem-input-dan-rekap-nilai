"""Business logic for user management."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories import user as user_repo
from app.schemas.user import UserCreate, UserUpdate
from app.services.auth import hash_password


async def create_user(db: AsyncSession, payload: UserCreate) -> User:
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
    return await user_repo.list_users(db, role=role, is_active=is_active)


async def update_user(db: AsyncSession, user_id: uuid.UUID, payload: UserUpdate) -> User:
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
    user = await get_user(db, user_id)
    user.is_active = False
    await user_repo.save(db, user)
