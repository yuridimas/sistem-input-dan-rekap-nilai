"""Persistence operations; services own component transactions.

Query dan persistence komponen kelas bagi service terkait.

Commit/rollback dimiliki service; error database diteruskan kecuali
disebutkan.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.class_ import Class
from app.models.component import Component


async def lock_class(db: AsyncSession, class_id: uuid.UUID) -> None:
    """Kunci kelas untuk menserialisasikan perubahan penilaian.

    Service memeriksa kelas absen, tanpa commit.

    SELECT FOR UPDATE.

    SELECT FOR UPDATE menahan lock hingga akhir transaksi. Kelas absen
    tidak menghasilkan lock; keberadaannya diperiksa service.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        class_id: UUID kelas yang menjadi cakupan operasi.
    """
    # Serialize changes to a class configuration, including its first insert.
    result = await db.execute(
        select(Class).where(Class.id == class_id).with_for_update()
        # Sesudah menunggu lock, objek session harus melihat pemilik/konfigurasi terbaru.
        .execution_options(populate_existing=True)
    )
    result.scalar_one_or_none()


async def get_by_id(db: AsyncSession, component_id: uuid.UUID) -> Component | None:
    """Muat ulang komponen agar identity map tidak usang.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        component_id: UUID komponen yang menjadi sasaran operasi.
    """
    return await db.get(Component, component_id, populate_existing=True)


async def list_by_class(db: AsyncSession, class_id: uuid.UUID) -> list[Component]:
    """Muat ulang urutan komponen editor secara deterministik.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        class_id: UUID kelas yang menjadi cakupan operasi.
    """
    result = await db.execute(
        select(Component).where(Component.class_id == class_id)
        .order_by(Component.order_index, Component.created_at, Component.id)
        .execution_options(populate_existing=True)
    )
    return list(result.scalars())


def add_all(db: AsyncSession, components: list[Component]) -> None:
    """Daftarkan komponen dalam transaksi konfigurasi service.

    Mengubah session tanpa flush/commit.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        components: Konfigurasi komponen kelas yang menjadi dasar
            penilaian.
    """
    db.add_all(components)


async def delete(db: AsyncSession, component: Component) -> None:
    """Jadwalkan penghapusan dalam transaksi konfigurasi.

    Tanpa commit.

    Constraint diperiksa saat service menyimpan.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        component: Objek komponen konfigurasi yang sedang diproses.
    """
    await db.delete(component)
