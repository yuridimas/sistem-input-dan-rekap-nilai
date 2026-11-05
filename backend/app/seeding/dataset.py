"""Append-only persistence for generated seed plans."""

from dataclasses import dataclass, field
import hashlib

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.course import Course
from app.models.class_ import Class
from app.models.student import Student
from app.models.component import Component
from app.models.enrollment import Enrollment
from app.models.score import Score
from app.models.grade import Grade
from app.models.ranking import Ranking
from app.models.notification import Notification
from app.seeding.scenarios import SeedPlan
from app.services.auth import hash_password


@dataclass(frozen=True)
class ApplyResult:
    """Outcome of appending or observing a named dataset."""

    status: str
    fingerprint: str
    counts: dict[str, int]
    missing: dict[str, int] = field(default_factory=dict)


async def apply_plan(db: AsyncSession, plan: SeedPlan, *, password: str) -> ApplyResult:
    """Append a dataset atomically; an existing anchor is strictly read-only."""
    lock_key = int.from_bytes(hashlib.sha256(plan.config.dataset.encode()).digest()[:8], "big", signed=True)
    await db.scalar(select(func.pg_advisory_xact_lock(lock_key)))
    existing = await db.get(User, plan.anchor_id)
    if existing is not None:
        return ApplyResult("existing", plan.fingerprint, plan.counts)

    async with db.begin_nested():
        objects = list(plan.objects)
        for obj in objects:
            if isinstance(obj, User):
                obj.password_hash = hash_password(password)
        # Models intentionally avoid ORM relationships; flush in explicit FK order.
        for model in (User, Course, Class, Student, Component, Enrollment,
                      Score, Grade, Ranking, Notification):
            batch = [obj for obj in objects if isinstance(obj, model)]
            if batch:
                db.add_all(batch)
                await db.flush()
    await db.commit()
    return ApplyResult("created", plan.fingerprint, plan.counts)


async def inspect_plan(db: AsyncSession, plan: SeedPlan) -> ApplyResult:
    """Report whether the anchor exists without creating or changing rows."""
    existing = await db.scalar(select(User.id).where(User.id == plan.anchor_id))
    expected: dict[type, list] = {}
    for obj in plan.objects:
        expected.setdefault(type(obj), []).append(obj.id)
    missing: dict[str, int] = {}
    for model, ids in expected.items():
        found = set((await db.scalars(select(model.id).where(model.id.in_(ids)))).all())
        absent = len(set(ids) - found)
        if absent:
            missing[model.__tablename__] = absent
    if not existing:
        status = "missing"
    else:
        status = "incomplete" if missing else "existing"
    return ApplyResult(status, plan.fingerprint, plan.counts, missing)
