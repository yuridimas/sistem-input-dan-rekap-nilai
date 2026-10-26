"""Class component configuration endpoints.

Adapter HTTP konfigurasi komponen yang didaftarkan app.main.

Dependency menetapkan identitas/role; aturan bisnis dan persistence
didelegasikan ke service.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User
from app.schemas.component import ComponentCreate, ComponentRead, ComponentUpdate, ComponentWrite
from app.services import component as service

router = APIRouter(tags=["components"])
_roles = require_role("superadmin", "lecturer")


@router.get("/classes/{class_id}/components", response_model=list[ComponentRead])
async def list_components(
    class_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(_roles),
) -> list[ComponentRead]:
    """Sajikan konfigurasi komponen kelas yang diizinkan.

    \f

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        class_id: UUID kelas yang menjadi cakupan operasi.
        db: Session database; batas commit mengikuti operasi terkait.
        user: Objek akun untuk pemeriksaan akses atau persistence sesuai
            operasi.

    Returns:
        Daftar konfigurasi komponen kelas; bisa kosong.
    """
    rows = await service.list_components(db, class_id, user)
    return [ComponentRead.model_validate(row) for row in rows]


@router.post("/classes/{class_id}/components", response_model=list[ComponentRead], status_code=201)
async def create_components(
    class_id: uuid.UUID,
    payload: Annotated[list[ComponentCreate], Body(min_length=1)],
    db: AsyncSession = Depends(get_db), user: User = Depends(_roles),
) -> list[ComponentRead]:
    """Tambahkan satu batch konfigurasi komponen yang valid.

    \f

    Create components atomically; submit the initial UTS/UAS set as a
    JSON array.

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        class_id: UUID kelas yang menjadi cakupan operasi.
        payload: Data masukan yang sudah melewati validasi schema
            endpoint.
        db: Session database; batas commit mengikuti operasi terkait.
        user: Objek akun untuk pemeriksaan akses atau persistence sesuai
            operasi.

    Returns:
        Konfigurasi komponen yang baru disimpan.
    """
    rows = await service.create_components(db, class_id, payload, user)
    return [ComponentRead.model_validate(row) for row in rows]


@router.patch("/components/{component_id}", response_model=ComponentRead)
async def update_component(
    component_id: uuid.UUID, payload: ComponentUpdate,
    db: AsyncSession = Depends(get_db), user: User = Depends(_roles),
) -> ComponentRead:
    """Ubah komponen tanpa membatalkan validitas skor tersimpan.

    \f

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        component_id: UUID komponen yang menjadi sasaran operasi.
        payload: Data masukan yang sudah melewati validasi schema
            endpoint.
        db: Session database; batas commit mengikuti operasi terkait.
        user: Objek akun untuk pemeriksaan akses atau persistence sesuai
            operasi.

    Returns:
        Konfigurasi komponen setelah perubahan.
    """
    row = await service.update_component(db, component_id, payload, user)
    return ComponentRead.model_validate(row)


@router.put("/classes/{class_id}/components", response_model=list[ComponentRead])
async def replace_components(
    class_id: uuid.UUID,
    payload: Annotated[list[ComponentWrite], Body(min_length=1)],
    db: AsyncSession = Depends(get_db), user: User = Depends(_roles),
) -> list[ComponentRead]:
    """Ganti konfigurasi lengkap dengan mempertahankan ID lama.

    \f

    Replace the full set atomically, keeping IDs supplied for existing
    components.

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        class_id: UUID kelas yang menjadi cakupan operasi.
        payload: Data masukan yang sudah melewati validasi schema
            endpoint.
        db: Session database; batas commit mengikuti operasi terkait.
        user: Objek akun untuk pemeriksaan akses atau persistence sesuai
            operasi.

    Returns:
        Konfigurasi lengkap setelah penggantian set.
    """
    rows = await service.replace_components(db, class_id, payload, user)
    return [ComponentRead.model_validate(row) for row in rows]


@router.delete("/components/{component_id}", status_code=204)
async def delete_component(
    component_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(_roles),
) -> Response:
    """Hapus komponen jika konfigurasi kelas tetap valid.

    \f

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        component_id: UUID komponen yang menjadi sasaran operasi.
        db: Session database; batas commit mengikuti operasi terkait.
        user: Objek akun untuk pemeriksaan akses atau persistence sesuai
            operasi.

    Returns:
        Respons HTTP 204 tanpa body.
    """
    await service.delete_component(db, component_id, user)
    return Response(status_code=204)
