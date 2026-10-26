"""Score queries and PostgreSQL upserts without committing transactions.

Query dan persistence skor komponen bagi service terkait.

Commit/rollback dimiliki service; error database diteruskan kecuali
disebutkan.
"""

import uuid
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enrollment import Enrollment
from app.models.score import Score


async def get_enrollment(db: AsyncSession, enrollment_id: uuid.UUID, *, lock: bool = False) -> Enrollment | None:
    """Muat ulang enrollment; lock True mengunci hingga akhir transaksi.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        enrollment_id: UUID keikutsertaan mahasiswa pada satu kelas.
        lock: True untuk menahan row lock sampai transaksi selesai.

    Returns:
        Enrollment terbaru, atau None jika tidak ditemukan.
    """
    stmt = select(Enrollment).where(Enrollment.id == enrollment_id).execution_options(populate_existing=True)
    if lock:
        stmt = stmt.with_for_update()
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_by_enrollment(db: AsyncSession, enrollment_id: uuid.UUID) -> list[Score]:
    """Muat ulang skor satu enrollment untuk kalkulasi total.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        enrollment_id: UUID keikutsertaan mahasiswa pada satu kelas.
    """
    result = await db.execute(
        select(Score).where(Score.enrollment_id == enrollment_id).execution_options(populate_existing=True)
    )
    return list(result.scalars())


async def list_by_class(db: AsyncSession, class_id: uuid.UUID) -> list[Score]:
    """Muat ulang skor kelas untuk validasi dan finalisasi.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        class_id: UUID kelas yang menjadi cakupan operasi.
    """
    result = await db.execute(
        select(Score).join(Enrollment, Enrollment.id == Score.enrollment_id)
        .where(Enrollment.class_id == class_id).execution_options(populate_existing=True)
    )
    return list(result.scalars())


async def upsert(
    db: AsyncSession, enrollment_id: uuid.UUID, values: dict[uuid.UUID, Decimal], entered_by: uuid.UUID,
) -> None:
    """Tulis skor parsial melalui constraint unik enrollment/komponen.

    Values kosong tidak menulis.

    Tanpa commit, memperbarui entered_by dan waktu audit.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        enrollment_id: UUID keikutsertaan mahasiswa pada satu kelas.
        values: Skor Decimal yang disimpan; mapping kosong tidak menulis
            data.
        entered_by: UUID pengguna yang dicatat sebagai pengubah skor
            terakhir.
    """
    if not values:
        return
    stmt = insert(Score).values([
        {"enrollment_id": enrollment_id, "component_id": component_id, "score": value, "entered_by": entered_by}
        for component_id, value in values.items()
    ])
    await db.execute(stmt.on_conflict_do_update(
        constraint="uq_scores_enrollment_component",
        set_={"score": stmt.excluded.score, "entered_by": stmt.excluded.entered_by,
              # Waktu aktual dipakai karena now() tetap sama sepanjang satu transaksi.
              "updated_at": func.clock_timestamp()},
    ))


async def clear(db: AsyncSession, enrollment_id: uuid.UUID, component_ids: list[uuid.UUID]) -> None:
    """Hapus skor komponen yang diminta secara idempotent.

    Input kosong tidak menulis.

    Tanpa commit, skor komponen lain tetap utuh.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        enrollment_id: UUID keikutsertaan mahasiswa pada satu kelas.
        component_ids: UUID komponen yang skornya dihapus; boleh kosong.
    """
    if component_ids:
        await db.execute(delete(Score).where(
            Score.enrollment_id == enrollment_id, Score.component_id.in_(component_ids),
        ))
