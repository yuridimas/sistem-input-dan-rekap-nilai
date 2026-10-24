"""Persistence operations; services own component transactions."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.class_ import Class
from app.models.component import Component


async def lock_class(db: AsyncSession, class_id: uuid.UUID) -> None:
    # Serialize changes to a class configuration, including its first insert.
    result = await db.execute(
        select(Class).where(Class.id == class_id).with_for_update()
        .execution_options(populate_existing=True)
    )
    result.scalar_one_or_none()


async def get_by_id(db: AsyncSession, component_id: uuid.UUID) -> Component | None:
    return await db.get(Component, component_id, populate_existing=True)


async def list_by_class(db: AsyncSession, class_id: uuid.UUID) -> list[Component]:
    result = await db.execute(
        select(Component).where(Component.class_id == class_id)
        .order_by(Component.order_index, Component.created_at, Component.id)
        .execution_options(populate_existing=True)
    )
    return list(result.scalars())


def add_all(db: AsyncSession, components: list[Component]) -> None:
    db.add_all(components)


async def delete(db: AsyncSession, component: Component) -> None:
    await db.delete(component)
