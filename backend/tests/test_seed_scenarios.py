"""Run all generated positive and negative cases through the actual API."""

from copy import deepcopy
import json
import uuid
from unittest.mock import Mock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.database import AsyncSessionLocal
from app.models.component import Component
from app.models.enrollment import Enrollment
from app.models.grade import Grade
from app.models.score import Score
from app.models.student import Student
from app.seeding.scenarios import GENERATED_CASES
from app.main import app
from app.services import reports as report_service
from app.services.release_notifications import celery_app


async def _state_for(sample):
    """Read the database state guarded by a negative or conflict sample."""
    async with AsyncSessionLocal() as session:
        if "score_unchanged" in sample.assertion_keys:
            component_id, _value = next(iter(sample.payload.items()))
            return await session.scalar(select(Score.score).where(
                Score.enrollment_id == uuid.UUID(sample.path.split("/")[2]),
                Score.component_id == uuid.UUID(component_id),
            ))
        if "component_unchanged" in sample.assertion_keys:
            component_id = uuid.UUID(sample.path.rsplit("/", 1)[1])
            component = await session.get(Component, component_id)
            return (component.name, component.weight) if component else None
        if "student_unchanged" in sample.assertion_keys:
            student_id = uuid.UUID(sample.path.rsplit("/", 1)[1])
            student = await session.get(Student, student_id)
            return (student.full_name, student.email) if student else None
        if "roster_unchanged" in sample.assertion_keys:
            class_id = uuid.UUID(sample.path.split("/")[2])
            return await session.scalar(select(func.count()).select_from(Enrollment).where(
                Enrollment.class_id == class_id,
            ))
        if "grade_remains_draft" in sample.assertion_keys or "grade_remains_final" in sample.assertion_keys:
            class_id = uuid.UUID(sample.path.split("/")[2])
            return await session.scalar(select(Grade.status).join(
                Enrollment, Enrollment.id == Grade.enrollment_id,
            ).where(Enrollment.class_id == class_id))
    return None


@pytest.mark.parametrize("case", GENERATED_CASES, ids=lambda case: case.case_id)
@pytest.mark.asyncio
async def test_generated_case(case, seeded_context, monkeypatch):
    plan, client, actors = seeded_context
    monkeypatch.setattr(celery_app, "send_task", Mock(return_value=None))

    async def render_pdf_stub(*_args, **_kwargs):
        return b"%PDF-1.7 generated API response stub"

    monkeypatch.setattr(report_service, "render_pdf", render_pdf_stub)
    samples = [sample for sample in plan.samples if sample.case_id == case.case_id]
    assert len(samples) >= plan.config.min_samples

    for sample in samples:
        payload = deepcopy(sample.payload)
        if isinstance(payload, dict):
            for key, value in payload.items():
                if value == "<SEED_PASSWORD>":
                    payload[key] = "pytest-seed-only-password"
        headers = actors.get(sample.actor_key, {})
        before = await _state_for(sample) if len(sample.assertion_keys) > 1 else None
        response = await client.request(sample.method, sample.path,
                                        json=payload if isinstance(payload, dict) else None,
                                        headers=headers)
        assert response.status_code == sample.expected_status, (
            sample.sample_id, response.status_code, response.text[:500]
        )
        if len(sample.assertion_keys) > 1:
            after = await _state_for(sample)
            assert after == before, (sample.sample_id, sample.assertion_keys, before, after)
            if "grade_remains_draft" in sample.assertion_keys:
                assert after == "draft"
            elif "grade_remains_final" in sample.assertion_keys:
                assert after == "finalized"
        if case.case_id.startswith("reports.") and response.status_code == 200:
            assert response.headers.get("content-disposition", "").startswith("attachment;")
            assert response.content
        elif response.headers.get("content-type", "").startswith("application/json") and response.content:
            assert isinstance(response.json(), (dict, list))


@pytest.mark.asyncio
async def test_manifest_samples_have_no_unresolved_resource_ids(seeded_context):
    plan, _client, _actors = seeded_context
    serialized = json.dumps([(sample.path, sample.payload) for sample in plan.samples])
    assert "${" not in serialized


@pytest.mark.asyncio
async def test_login_rate_limit_still_rejects_the_31st_request():
    transport = ASGITransport(app=app, client=("198.51.100.31", 5000))
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        responses = [
            await client.post("/auth/login", json={
                "email": "rate-limit-nobody@example.test", "password": "invalid-password",
            })
            for _ in range(31)
        ]
    assert all(response.status_code == 401 for response in responses[:30])
    assert responses[30].status_code == 429
