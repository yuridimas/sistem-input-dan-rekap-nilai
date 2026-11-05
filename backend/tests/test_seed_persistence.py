"""Persistent seed application never overwrites human edits or cleans rows."""

import asyncio
import uuid
from unittest.mock import Mock

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.student import Student
from app.models.user import User
from app.seeding.config import resolve_config
from app.seeding.dataset import apply_plan
from app.seeding.scenarios import build_plan
from app.services import mailer
from app.services.release_notifications import celery_app


@pytest.mark.asyncio
async def test_apply_is_append_only_and_preserves_human_edits(monkeypatch):
    plan = build_plan(resolve_config(dataset=f"pytest-persist-{uuid.uuid4().hex[:8]}", seed=20261105,
                                     min_samples=5, max_samples=5))
    send_task = Mock(side_effect=AssertionError("task published"))
    send_email = Mock(side_effect=AssertionError("email sent"))
    monkeypatch.setattr(celery_app, "send_task", send_task)
    monkeypatch.setattr(mailer, "send_grade_email", send_email)
    async with AsyncSessionLocal() as session:
        result = await apply_plan(session, plan, password="test-only-seed-password")
        assert result.status == "created"
        student_id = next(obj.id for obj in plan.objects
                          if isinstance(obj, Student))
        student = await session.scalar(select(Student).where(Student.id == student_id))
        assert student is not None
        student.full_name = "Human edited persistent fixture"
        await session.commit()

    async with AsyncSessionLocal() as session:
        result = await apply_plan(session, plan, password="another-test-password")
        assert result.status == "existing"
        student = await session.scalar(select(Student).where(Student.id == student_id))
        assert student is not None
        assert student.full_name == "Human edited persistent fixture"
    send_task.assert_not_called()
    send_email.assert_not_called()


@pytest.mark.asyncio
async def test_simultaneous_apply_keeps_one_dataset_winner():
    config = resolve_config(dataset=f"pytest-concurrent-{uuid.uuid4().hex[:8]}", seed=20261105,
                            min_samples=5, max_samples=5)

    async def apply_once():
        async with AsyncSessionLocal() as session:
            return await apply_plan(session, build_plan(config), password="test-only-seed-password")

    results = await asyncio.gather(apply_once(), apply_once())
    assert sorted(result.status for result in results) == ["created", "existing"]


@pytest.mark.asyncio
async def test_natural_key_conflict_rolls_back_only_the_new_dataset():
    plan = build_plan(resolve_config(dataset=f"pytest-conflict-{uuid.uuid4().hex[:8]}",
                                     seed=20261105, min_samples=5, max_samples=5))
    intended_admin = next(obj for obj in plan.objects
                          if isinstance(obj, User) and obj.email.startswith("admin-"))
    conflict = User(id=uuid.uuid4(), email=intended_admin.email,
                    password_hash="test-only", full_name="Existing row",
                    role="superadmin", is_active=True)
    async with AsyncSessionLocal() as session:
        session.add(conflict)
        await session.commit()

    async with AsyncSessionLocal() as session:
        with pytest.raises(IntegrityError):
            await apply_plan(session, plan, password="test-only-seed-password")
        await session.rollback()

    async with AsyncSessionLocal() as session:
        existing = await session.get(User, conflict.id)
        anchor = await session.get(User, plan.anchor_id)
        assert existing is not None and existing.full_name == "Existing row"
        assert anchor is None
