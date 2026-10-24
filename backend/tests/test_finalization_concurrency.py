"""Real multi-connection serialization of grade release and roster writes."""

import asyncio
import uuid
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.database import AsyncSessionLocal
from app.main import app
from app.models.class_ import Class
from app.models.component import Component
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.grade import Grade
from app.models.ranking import Ranking
from app.models.score import Score
from app.models.student import Student
from app.models.user import User
from app.repositories import component as component_repo
from app.services.auth import create_access_token


@pytest_asyncio.fixture(loop_scope="session")
async def release_context(monkeypatch):
    user_id, course_id, class_id, enrollment_id = [uuid.uuid4() for _ in range(4)]
    student_ids = [uuid.uuid4(), uuid.uuid4()]
    component_ids = [uuid.uuid4() for _ in range(3)]
    suffix = uuid.uuid4().hex
    published = []

    async def publish(ids):
        published.extend(ids)
        return len(ids)

    monkeypatch.setattr("app.services.grade.publish_grade_releases", publish)
    try:
        async with AsyncSessionLocal() as db:
            db.add(User(id=user_id, email=f"release-{suffix}@example.com", full_name="Dosen",
                        role="lecturer", password_hash="unused"))
            await db.flush()
            db.add(Course(id=course_id, code=f"REL-{suffix}", name="Rilis", credits=3,
                          semester="2026/1", created_by=user_id))
            await db.flush()
            db.add(Class(id=class_id, course_id=course_id, lecturer_id=user_id,
                         section="A", academic_year="2026/2027"))
            db.add_all([Student(id=student_id, nim=f"{index}-{suffix}", full_name=f"Mahasiswa {index}")
                        for index, student_id in enumerate(student_ids)])
            await db.flush()
            db.add(Enrollment(id=enrollment_id, class_id=class_id, student_id=student_ids[0]))
            db.add_all([
                Component(id=component_id, class_id=class_id, name=category, category=category,
                          weight=weight, max_score=100)
                for component_id, category, weight in zip(component_ids, ("tugas", "uts", "uas"), (30, 30, 40))
            ])
            await db.commit()
        headers = {"Authorization": "Bearer " + create_access_token(str(user_id), "lecturer")}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(f"/enrollments/{enrollment_id}/scores", headers=headers,
                                        json={str(key): value for key, value in zip(component_ids, (80, 70, 90))})
            assert response.status_code == 200, response.text
            yield client, class_id, enrollment_id, component_ids, headers, f"1-{suffix}", published, course_id, user_id
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(Ranking).where(Ranking.class_id == class_id))
            enrollment_ids = select(Enrollment.id).where(Enrollment.class_id == class_id)
            await db.execute(delete(Score).where(Score.enrollment_id.in_(enrollment_ids)))
            await db.execute(delete(Grade).where(Grade.enrollment_id.in_(enrollment_ids)))
            await db.execute(delete(Component).where(Component.class_id == class_id))
            await db.execute(delete(Enrollment).where(Enrollment.class_id == class_id))
            await db.execute(delete(Class).where(Class.course_id == course_id))
            await db.execute(delete(Course).where(Course.id == course_id))
            await db.execute(delete(Student).where(Student.id.in_(student_ids)))
            await db.execute(delete(User).where(User.id == user_id))
            await db.commit()


@pytest.mark.asyncio
@pytest.mark.parametrize("first_action,second_action,statuses", [
    ("finalize", "finalize", (202, 409)),
    ("score", "finalize", (200, 202)),
    ("finalize", "score", (202, 409)),
    ("enroll", "finalize", (201, 422)),
    ("finalize", "enroll", (202, 409)),
    ("delete", "finalize", (204, 202)),
    ("finalize", "delete", (202, 409)),
])
async def test_release_serializes_with_mutations(release_context, monkeypatch, first_action, second_action, statuses):
    client, class_id, enrollment_id, component_ids, headers, extra_nim, published, _course_id, _user_id = release_context
    delete_id = enrollment_id
    if first_action == "delete":
        # Removing an unscored extra student must complete before the completeness check.
        response = await client.post(f"/classes/{class_id}/enrollments", headers=headers, json={"nim": extra_nim})
        assert response.status_code == 201, response.text
        delete_id = response.json()["id"]
    original_lock = component_repo.lock_class
    first_locked, second_started = asyncio.Event(), asyncio.Event()
    calls = 0

    async def ordered_lock(db, target_id):
        nonlocal calls
        calls += 1
        if calls == 1:
            await original_lock(db, target_id)
            first_locked.set()
            await second_started.wait()
        else:
            second_started.set()
            await original_lock(db, target_id)

    monkeypatch.setattr(component_repo, "lock_class", ordered_lock)

    async def request(action):
        if action == "finalize":
            return await client.post(f"/classes/{class_id}/finalize", headers=headers)
        if action == "score":
            return await client.put(f"/enrollments/{enrollment_id}/scores", headers=headers,
                                    json={str(component_ids[0]): "100"})
        if action == "enroll":
            return await client.post(f"/classes/{class_id}/enrollments", headers=headers, json={"nim": extra_nim})
        return await client.delete(f"/classes/{class_id}/enrollments/{delete_id}", headers=headers)

    tasks = [asyncio.create_task(request(first_action))]
    try:
        await asyncio.wait_for(first_locked.wait(), timeout=10)
        tasks.append(asyncio.create_task(request(second_action)))
        first, second = await asyncio.wait_for(asyncio.gather(*tasks), timeout=10)
        assert (first.status_code, second.status_code) == statuses, (first.text, second.text)
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
    ranking = (await client.get(f"/classes/{class_id}/ranking", headers=headers)).json()
    if 202 in statuses:
        assert len(ranking) == 1 and ranking[0]["rank"] == 1
        assert Decimal(ranking[0]["final_score"]) == Decimal("87" if first_action == "score" else "81")
        assert len(published) == 1
    else:
        assert ranking == [] and published == []


@pytest.mark.asyncio
async def test_enrollment_of_new_student_holds_class_lock_until_commit(release_context, monkeypatch):
    from app.repositories import enrollment as enrollment_repo

    client, class_id, _enrollment, _components, headers, _nim, _published, _course, _user = release_context
    original_add = enrollment_repo.add
    student_flushed, finalizer_started = asyncio.Event(), asyncio.Event()
    new_nim = f"new-{uuid.uuid4().hex}"
    original_lock = component_repo.lock_class
    locks = 0

    async def observe_lock(db, target_id):
        nonlocal locks
        locks += 1
        if locks == 2:
            finalizer_started.set()
        await original_lock(db, target_id)

    async def pause_enrollment(db, enrollment):
        student_flushed.set()
        await finalizer_started.wait()
        return await original_add(db, enrollment)

    monkeypatch.setattr(component_repo, "lock_class", observe_lock)
    monkeypatch.setattr(enrollment_repo, "add", pause_enrollment)
    tasks = [asyncio.create_task(client.post(f"/classes/{class_id}/enrollments", headers=headers, json={"nim": new_nim}))]
    try:
        await asyncio.wait_for(student_flushed.wait(), timeout=10)
        tasks.append(asyncio.create_task(client.post(f"/classes/{class_id}/finalize", headers=headers)))
        enrollment, release = await asyncio.wait_for(asyncio.gather(*tasks), timeout=10)
        assert enrollment.status_code == 201, enrollment.text
        assert release.status_code == 422, release.text
        assert any(row["student_nim"] == new_nim for row in release.json()["detail"]["missing"])
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        # The fixture owns enrolled rows; this extra student's identity is unique to this test.
        async with AsyncSessionLocal() as db:
            extra_student = select(Student.id).where(Student.nim == new_nim)
            await db.execute(delete(Enrollment).where(Enrollment.class_id == class_id, Enrollment.student_id.in_(extra_student)))
            await db.execute(delete(Student).where(Student.nim == new_nim))
            await db.commit()


@pytest.mark.asyncio
async def test_concurrent_new_nim_reuses_student_without_releasing_class_lock(release_context, monkeypatch):
    from app.repositories import student as student_repo

    client, class_id, _enrollment, _components, headers, _nim, _published, course_id, _user = release_context
    response = await client.post("/classes", headers=headers, json={
        "course_id": str(course_id), "section": "B", "academic_year": "2026/2027",
    })
    assert response.status_code == 201, response.text
    second_class = response.json()["id"]
    nim = f"race-{uuid.uuid4().hex}"
    original_get = student_repo.get_by_nim
    both_missing = asyncio.Event()
    misses = 0

    async def synchronized_lookup(db, target_nim):
        nonlocal misses
        result = await original_get(db, target_nim)
        if target_nim == nim and result is None:
            misses += 1
            if misses == 2:
                both_missing.set()
            await both_missing.wait()
        return result

    monkeypatch.setattr(student_repo, "get_by_nim", synchronized_lookup)
    tasks = [asyncio.create_task(client.post(f"/classes/{target}/enrollments", headers=headers, json={"nim": nim}))
             for target in (class_id, second_class)]
    try:
        first, second = await asyncio.wait_for(asyncio.gather(*tasks), timeout=10)
        assert first.status_code == second.status_code == 201, (first.text, second.text)
        assert first.json()["student"]["id"] == second.json()["student"]["id"]
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        async with AsyncSessionLocal() as db:
            matching_student = select(Student.id).where(Student.nim == nim)
            await db.execute(delete(Enrollment).where(Enrollment.student_id.in_(matching_student)))
            await db.execute(delete(Student).where(Student.nim == nim))
            await db.commit()
