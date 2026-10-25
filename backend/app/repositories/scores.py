"""Score queries and PostgreSQL upserts without committing transactions."""

import uuid
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enrollment import Enrollment
from app.models.score import Score


async def get_enrollment(db: AsyncSession, enrollment_id: uuid.UUID, *, lock: bool = False) -> Enrollment | None:
    stmt = select(Enrollment).where(Enrollment.id == enrollment_id).execution_options(populate_existing=True)
    if lock:
        stmt = stmt.with_for_update()
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_by_enrollment(db: AsyncSession, enrollment_id: uuid.UUID) -> list[Score]:
    result = await db.execute(
        select(Score).where(Score.enrollment_id == enrollment_id).execution_options(populate_existing=True)
    )
    return list(result.scalars())


async def list_by_class(db: AsyncSession, class_id: uuid.UUID) -> list[Score]:
    result = await db.execute(
        select(Score).join(Enrollment, Enrollment.id == Score.enrollment_id)
        .where(Enrollment.class_id == class_id).execution_options(populate_existing=True)
    )
    return list(result.scalars())


async def upsert(
    db: AsyncSession, enrollment_id: uuid.UUID, values: dict[uuid.UUID, Decimal], entered_by: uuid.UUID,
) -> None:
    if not values:
        return
    stmt = insert(Score).values([
        {"enrollment_id": enrollment_id, "component_id": component_id, "score": value, "entered_by": entered_by}
        for component_id, value in values.items()
    ])
    await db.execute(stmt.on_conflict_do_update(
        constraint="uq_scores_enrollment_component",
        set_={"score": stmt.excluded.score, "entered_by": stmt.excluded.entered_by,
              "updated_at": func.clock_timestamp()},
    ))


async def clear(db: AsyncSession, enrollment_id: uuid.UUID, component_ids: list[uuid.UUID]) -> None:
    if component_ids:
        await db.execute(delete(Score).where(
            Score.enrollment_id == enrollment_id, Score.component_id.in_(component_ids),
        ))
