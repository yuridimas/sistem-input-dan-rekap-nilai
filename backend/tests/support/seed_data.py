"""Persistent disposable-database context for generated request samples."""

import uuid

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.seeding.config import resolve_config
from app.seeding.dataset import apply_plan
from app.seeding.scenarios import SeedPlan, build_plan
from app.services.auth import create_access_token


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def seeded_context() -> tuple[SeedPlan, AsyncClient, dict[str, dict[str, str]]]:
    """Append one non-cleaned generated dataset to the explicitly disposable DB."""
    from app.main import app

    dataset = f"pytest-api-{uuid.uuid4().hex[:8]}"
    config = resolve_config(dataset=dataset, seed=20261105)
    plan = build_plan(config)
    async with AsyncSessionLocal() as session:
        await apply_plan(session, plan, password="pytest-seed-only-password")
    lecturer = next(obj for obj in plan.objects
                    if isinstance(obj, User) and obj.email.startswith("lecturer-"))
    superadmin = next(obj for obj in plan.objects
                      if isinstance(obj, User) and obj.email.startswith("admin-"))
    actors = {
        "lecturer": {"Authorization": f"Bearer {create_access_token(str(lecturer.id), UserRole.LECTURER.value)}"},
        "superadmin": {"Authorization": f"Bearer {create_access_token(str(superadmin.id), UserRole.SUPERADMIN.value)}"},
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield plan, client, actors
