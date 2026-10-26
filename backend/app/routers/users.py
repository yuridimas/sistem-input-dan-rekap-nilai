"""Superadmin user-management router.

Adapter HTTP akun administratif yang didaftarkan app.main.

Dependency menetapkan identitas/role; aturan bisnis dan persistence
didelegasikan ke service.
"""

import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services import user as user_service

router = APIRouter(
    prefix="/admin/users",
    tags=["admin-users"],
    dependencies=[Depends(require_role("superadmin"))],
)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    """Buat akun tanpa mengekspos hash password pada respons.

    \f

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        payload: Data masukan yang sudah melewati validasi schema
            endpoint.
        db: Session database; batas commit mengikuti operasi terkait.

    Returns:
        Profil akun baru tanpa hash password.
    """
    user = await user_service.create_user(db, payload)
    return UserRead.model_validate(user)


@router.get("", response_model=list[UserRead])
async def list_users(
    role: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[UserRead]:
    """Sajikan akun administratif dengan filter opsional.

    \f

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        role: Role akun atau filter role yang dipakai operasi.
        is_active: Filter status akun; None menyertakan kedua status.
        db: Session database; batas commit mengikuti operasi terkait.

    Returns:
        Daftar akun sesuai filter; bisa kosong.
    """
    users = await user_service.list_users(db, role=role, is_active=is_active)
    return [UserRead.model_validate(user) for user in users]


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    """Sajikan profil administratif tanpa informasi password.

    \f

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        user_id: Identitas akun yang dicari atau dikelola.
        db: Session database; batas commit mengikuti operasi terkait.

    Returns:
        Profil administratif tanpa hash password.
    """
    user = await user_service.get_user(db, user_id)
    return UserRead.model_validate(user)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    """Ubah akun atau password melalui service pengguna.

    \f

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        user_id: Identitas akun yang dicari atau dikelola.
        payload: Data masukan yang sudah melewati validasi schema
            endpoint.
        db: Session database; batas commit mengikuti operasi terkait.

    Returns:
        Profil administratif setelah perubahan.
    """
    user = await user_service.update_user(db, user_id, payload)
    return UserRead.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Nonaktifkan akun sambil mempertahankan relasi historis.

    \f

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        user_id: Identitas akun yang dicari atau dikelola.
        db: Session database; batas commit mengikuti operasi terkait.

    Returns:
        Respons HTTP 204 tanpa body setelah penonaktifan.
    """
    await user_service.deactivate_user(db, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
