"""Validate complete component configurations before persisting changes.

Koordinasi perubahan komponen penilaian bagi router components.

Validasi proyeksi konfigurasi dan hitung ulang draft sebelum repository
menyimpan perubahan.
"""

import uuid

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.component import Component
from app.models.user import User
from app.repositories import component as repo
from app.schemas.component import ComponentCreate, ComponentUpdate, ComponentWrite
from app.services.class_ import get_class
from app.services import grade as grade_service
from app.services.component_rules import validate_configuration


def _configuration(component: Component, changes: dict | None = None) -> ComponentCreate:
    """Bentuk proyeksi konfigurasi tanpa mutasi objek ORM.

    Tidak menulis database.

    Args:
        component: Objek komponen konfigurasi yang sedang diproses.
        changes: Field pengganti opsional; None mempertahankan
            konfigurasi asal.

    Raises:
        ValidationError: bila proyeksi melanggar schema.
    """
    return ComponentCreate.model_validate({
        "name": component.name, "category": component.category, "weight": component.weight,
        "max_score": component.max_score, "order_index": component.order_index,
        **(changes or {}),
    })


async def list_components(db: AsyncSession, class_id: uuid.UUID, user: User) -> list[Component]:
    """Baca konfigurasi setelah pemeriksaan akses kelas.

    Tidak menulis database.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        class_id: UUID kelas yang menjadi cakupan operasi.
        user: Objek akun untuk pemeriksaan akses atau persistence sesuai
            operasi.

    Returns:
        List[Component], bisa kosong.

    Raises:
        HTTPException: 403/404 dari get_class.
    """
    await get_class(db, class_id, user)
    return await repo.list_by_class(db, class_id)


async def create_components(
    db: AsyncSession, class_id: uuid.UUID, payload: list[ComponentCreate], user: User,
) -> list[Component]:
    """Tambahkan komponen hanya jika konfigurasi gabungan valid.

    Lock dan commit DB; HTTPException untuk akses, finalisasi,
    konfigurasi, atau konflik.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        class_id: UUID kelas yang menjadi cakupan operasi.
        payload: Data masukan yang sudah melewati validasi schema
            endpoint.
        user: Objek akun untuk pemeriksaan akses atau persistence sesuai
            operasi.
    """
    await repo.lock_class(db, class_id)
    await get_class(db, class_id, user)
    await grade_service.ensure_components_mutable(db, class_id)
    existing = await repo.list_by_class(db, class_id)
    validate_configuration([_configuration(row) for row in existing] + payload)
    rows = [Component(class_id=class_id, **item.model_dump()) for item in payload]
    repo.add_all(db, rows)
    await _commit(db, class_id)
    for row in rows:
        await db.refresh(row)
    return rows


async def _get_component(db: AsyncSession, component_id: uuid.UUID, user: User) -> Component:
    """Muat ulang komponen setelah lock dan pemeriksaan akses.

    Lock kelas; HTTPException 403/404 untuk akses/data, 409 jika sudah
    final.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        component_id: UUID komponen yang menjadi sasaran operasi.
        user: Objek akun untuk pemeriksaan akses atau persistence sesuai
            operasi.

    Returns:
        Component yang masih boleh diubah.
    """
    component = await repo.get_by_id(db, component_id)
    if component is None:
        raise HTTPException(404, "Komponen penilaian tidak ditemukan")
    await repo.lock_class(db, component.class_id)
    await get_class(db, component.class_id, user)
    await grade_service.ensure_components_mutable(db, component.class_id)
    # A set replacement may have deleted this component before the lock was acquired.
    component = await repo.get_by_id(db, component_id)
    if component is None:
        raise HTTPException(404, "Komponen penilaian tidak ditemukan")
    return component


async def update_component(
    db: AsyncSession, component_id: uuid.UUID, payload: ComponentUpdate, user: User,
) -> Component:
    """Validasi proyeksi konfigurasi sebelum menerapkan patch.

    Lock/commit dan hitung ulang draft; HTTPException bila
    akses/konfigurasi tidak valid.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        component_id: UUID komponen yang menjadi sasaran operasi.
        payload: Data masukan yang sudah melewati validasi schema
            endpoint.
        user: Objek akun untuk pemeriksaan akses atau persistence sesuai
            operasi.
    """
    component = await _get_component(db, component_id, user)
    # Field yang tidak dikirim tidak ikut menimpa konfigurasi tersimpan.
    changes = payload.model_dump(exclude_unset=True)
    rows = await repo.list_by_class(db, component.class_id)
    projected = {row.id: _configuration(row, changes if row.id == component_id else None) for row in rows}
    validate_configuration(list(projected.values()))
    await grade_service.validate_score_compatibility(
        db, component.class_id, {key: row.max_score for key, row in projected.items()},
    )
    for key, value in changes.items():
        setattr(component, key, value)
    await _commit(db, component.class_id)
    await db.refresh(component)
    return component


async def delete_component(db: AsyncSession, component_id: uuid.UUID, user: User) -> None:
    """Hapus komponen hanya jika konfigurasi tersisa valid.

    Lock/commit; HTTPException bila kelas final, konfigurasi gagal, atau
    data masih dirujuk.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        component_id: UUID komponen yang menjadi sasaran operasi.
        user: Objek akun untuk pemeriksaan akses atau persistence sesuai
            operasi.
    """
    component = await _get_component(db, component_id, user)
    rows = await repo.list_by_class(db, component.class_id)
    validate_configuration([_configuration(row) for row in rows if row.id != component_id])
    await repo.delete(db, component)
    await _commit(db, component.class_id)


async def replace_components(
    db: AsyncSession, class_id: uuid.UUID, payload: list[ComponentWrite], user: User,
) -> list[Component]:
    """Ganti konfigurasi lengkap dengan menjaga ID komponen lama.

    Lock/commit; HTTPException untuk ID asing/duplikat, skor tidak
    kompatibel, atau konflik.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        class_id: UUID kelas yang menjadi cakupan operasi.
        payload: Data masukan yang sudah melewati validasi schema
            endpoint.
        user: Objek akun untuk pemeriksaan akses atau persistence sesuai
            operasi.
    """
    await repo.lock_class(db, class_id)
    await get_class(db, class_id, user)
    await grade_service.ensure_components_mutable(db, class_id)
    existing = {row.id: row for row in await repo.list_by_class(db, class_id)}
    supplied_ids = [row.id for row in payload if row.id is not None]
    if len(set(supplied_ids)) != len(supplied_ids):
        raise HTTPException(422, "ID komponen tidak boleh berulang")
    if not set(supplied_ids).issubset(existing):
        raise HTTPException(422, "Komponen tidak ditemukan pada kelas ini")
    validate_configuration(payload)
    await grade_service.validate_score_compatibility(
        db, class_id, {row.id: row.max_score for row in payload if row.id is not None},
    )

    # Validate the entire request before mutating tracked rows.
    for row_id, row in existing.items():
        if row_id not in supplied_ids:
            await repo.delete(db, row)
    for item in payload:
        values = item.model_dump(exclude={"id"})
        if item.id is None:
            repo.add_all(db, [Component(class_id=class_id, **values)])
        else:
            for key, value in values.items():
                setattr(existing[item.id], key, value)
    await _commit(db, class_id)
    return await repo.list_by_class(db, class_id)


async def _commit(db: AsyncSession, class_id: uuid.UUID) -> None:
    """Simpan konfigurasi dan total draft dalam satu transaksi.

    Commit DB; rollback dan HTTPException 409 ketika constraint database
    menolak perubahan.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        class_id: UUID kelas yang menjadi cakupan operasi.
    """
    try:
        await grade_service.recalculate_class_drafts(db, class_id)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Komponen masih digunakan atau data kelas telah berubah")
