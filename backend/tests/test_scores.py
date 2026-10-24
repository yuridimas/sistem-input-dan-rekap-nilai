"""Score entry, draft calculations, audit data, and access boundaries."""

import asyncio
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine, get_db
from app.main import app
from app.models.class_ import Class
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.student import Student
from app.models.user import User
from app.services.auth import create_access_token, decode_token


@pytest_asyncio.fixture(loop_scope="session")
async def grading_context():
    async with engine.connect() as connection:
        transaction = await connection.begin()
        try:
            async with AsyncSession(
                bind=connection, expire_on_commit=False,
                join_transaction_mode="create_savepoint",
            ) as db:
                suffix = uuid.uuid4().hex
                users = [
                    User(email=f"scores-{index}-{suffix}@example.com", role=role,
                         full_name=role, password_hash="unused")
                    for index, role in enumerate(["lecturer", "lecturer", "superadmin"])
                ]
                db.add_all(users)
                await db.flush()
                course = Course(code=f"SCORE-{suffix}", name="Penilaian", credits=3,
                                semester="2026/1", created_by=users[0].id)
                db.add(course)
                await db.flush()
                class_ = Class(course_id=course.id, lecturer_id=users[0].id,
                               section="A", academic_year="2026/2027")
                db.add(class_)
                students = [Student(nim=f"{index}-{suffix}", full_name=f"Mahasiswa {index}")
                            for index in range(2)]
                db.add_all(students)
                await db.flush()
                enrollments = [Enrollment(class_id=class_.id, student_id=student.id)
                               for student in students]
                db.add_all(enrollments)
                await db.commit()

                async def override_db():
                    yield db

                app.dependency_overrides[get_db] = override_db
                headers = [
                    {"Authorization": "Bearer " + create_access_token(str(user.id), user.role)}
                    for user in users
                ]
                try:
                    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                        response = await client.post(
                            f"/classes/{class_.id}/components", headers=headers[0], json=[
                                {"name": "Tugas", "category": "tugas", "weight": "30", "order_index": 0},
                                {"name": "UTS", "category": "uts", "weight": "30", "order_index": 1},
                                {"name": "UAS", "category": "uas", "weight": "40", "order_index": 2},
                            ],
                        )
                        assert response.status_code == 201, response.text
                        yield client, str(class_.id), [str(row.id) for row in enrollments], response.json(), headers, db
                finally:
                    app.dependency_overrides.pop(get_db, None)
        finally:
            await transaction.rollback()


def score_payload(components, values=("80", "70", "90")):
    return {component["id"]: value for component, value in zip(components, values)}


@pytest.mark.asyncio
async def test_scores_compute_final_and_update_without_duplicates(grading_context):
    client, class_id, enrollments, components, (owner, _, admin), db = grading_context
    url = f"/enrollments/{enrollments[0]}/scores"
    response = await client.put(url, headers=owner, json=score_payload(components))
    assert response.status_code == 200, response.text
    grade = response.json()
    assert Decimal(grade["final_score"]) == Decimal("81.00")
    assert grade["status"] == "draft"
    assert grade["enrollment_id"] == enrollments[0]
    assert grade["finalized_at"] is None and grade["finalized_by"] is None

    first = (await db.execute(text(
        "SELECT id, entered_by, entered_at, updated_at FROM scores "
        "WHERE enrollment_id = :enrollment_id AND component_id = :component_id"
    ), {"enrollment_id": uuid.UUID(enrollments[0]), "component_id": uuid.UUID(components[0]["id"])})).one()
    owner_id = uuid.UUID(decode_token(owner["Authorization"].split()[1])["sub"])
    assert first.entered_by == owner_id

    response = await client.put(url, headers=admin, json={components[0]["id"]: "100"})
    assert response.status_code == 200, response.text
    assert response.json()["id"] == grade["id"]
    assert Decimal(response.json()["final_score"]) == Decimal("87.00")
    second = (await db.execute(text(
        "SELECT id, entered_by, entered_at, updated_at FROM scores "
        "WHERE enrollment_id = :enrollment_id AND component_id = :component_id"
    ), {"enrollment_id": uuid.UUID(enrollments[0]), "component_id": uuid.UUID(components[0]["id"])})).one()
    admin_id = uuid.UUID(decode_token(admin["Authorization"].split()[1])["sub"])
    assert second.id == first.id and second.entered_at == first.entered_at
    assert second.entered_by == admin_id and second.updated_at > first.updated_at
    count = await db.scalar(text("SELECT count(*) FROM scores WHERE enrollment_id = :id"),
                            {"id": uuid.UUID(enrollments[0])})
    assert count == 3

    response = await client.get(f"/classes/{class_id}/grades", headers=owner)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["class_id"] == class_id and data["components"] == components
    assert len(data["grades"]) == 2
    assert [row["student"]["nim"] for row in data["grades"]] == sorted(row["student"]["nim"] for row in data["grades"])
    assert Decimal(data["grades"][0]["final_score"]) == Decimal("87")
    assert {key: Decimal(value) for key, value in data["grades"][0]["scores"].items()} == {
        components[0]["id"]: Decimal("100"), components[1]["id"]: Decimal("70"),
        components[2]["id"]: Decimal("90"),
    }
    assert data["grades"][1]["scores"] == {}
    assert data["grades"][1]["final_score"] is None and data["grades"][1]["status"] == "draft"


@pytest.mark.asyncio
async def test_partial_scores_preserve_missing_and_zero_scores(grading_context):
    client, class_id, enrollments, components, (owner, _, _), _db = grading_context
    url = f"/enrollments/{enrollments[0]}/scores"
    response = await client.put(url, headers=owner, json={components[0]["id"]: "80"})
    assert response.status_code == 200, response.text
    assert Decimal(response.json()["final_score"]) == Decimal("24")
    response = await client.put(url, headers=owner, json={components[1]["id"]: "0"})
    assert response.status_code == 200, response.text
    data = (await client.get(f"/classes/{class_id}/grades", headers=owner)).json()["grades"][0]
    assert Decimal(data["scores"][components[1]["id"]]) == 0
    assert components[2]["id"] not in data["scores"]
    assert Decimal(data["final_score"]) == Decimal("24")


@pytest.mark.asyncio
@pytest.mark.parametrize("value", ["-0.01", "100.01", "NaN", "Infinity", "1.001", None, True, "invalid"])
async def test_invalid_scores_rejected_atomically(grading_context, value):
    client, class_id, enrollments, components, (owner, _, _), _db = grading_context
    response = await client.put(f"/enrollments/{enrollments[0]}/scores", headers=owner,
                                json={components[0]["id"]: "80", components[1]["id"]: value})
    assert response.status_code == 422, response.text
    row = (await client.get(f"/classes/{class_id}/grades", headers=owner)).json()["grades"][0]
    assert row["scores"] == {} and row["final_score"] is None


@pytest.mark.asyncio
async def test_scores_reject_unknown_components_and_empty_payload(grading_context):
    client, _class_id, enrollments, components, (owner, _, _), db = grading_context
    url = f"/enrollments/{enrollments[0]}/scores"
    for payload in ({}, {"bad-id": "80"}, {str(uuid.uuid4()): "80"}):
        response = await client.put(url, headers=owner, json=payload)
        assert response.status_code == 422, response.text
    # A real component from another class must also be rejected.
    from app.models.component import Component
    source_class = await db.get(Class, uuid.UUID(_class_id))
    other_class = Class(course_id=source_class.course_id, lecturer_id=source_class.lecturer_id,
                        section="B", academic_year=source_class.academic_year)
    db.add(other_class)
    await db.flush()
    other_component = Component(class_id=other_class.id, name="UTS", category="uts", weight=100)
    db.add(other_component)
    await db.commit()
    response = await client.put(url, headers=owner, json={other_component.id.hex: "90"})
    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_scores_require_class_access(grading_context):
    client, class_id, enrollments, components, (owner, other, admin), _db = grading_context
    url = f"/enrollments/{enrollments[0]}/scores"
    payload = score_payload(components)
    assert (await client.put(url, json=payload)).status_code == 401
    assert (await client.put(url, headers=other, json=payload)).status_code == 403
    assert (await client.get(f"/classes/{class_id}/grades", headers=other)).status_code == 403
    assert (await client.get(f"/classes/{class_id}/grades")).status_code == 401
    assert (await client.get(f"/classes/{uuid.uuid4()}/grades", headers=owner)).status_code == 404
    assert (await client.put(f"/enrollments/{uuid.uuid4()}/scores", headers=owner, json=payload)).status_code == 404
    assert (await client.put(url, headers=admin, json=payload)).status_code == 200


@pytest.mark.asyncio
async def test_nonstandard_maximum_and_decimal_rounding(grading_context):
    client, _class_id, enrollments, components, (owner, _, _), _db = grading_context
    response = await client.patch(f"/components/{components[0]['id']}", headers=owner,
                                  json={"max_score": "20"})
    assert response.status_code == 200, response.text
    url = f"/enrollments/{enrollments[0]}/scores"
    assert (await client.put(url, headers=owner, json={components[0]["id"]: "20.01"})).status_code == 422
    response = await client.put(url, headers=owner, json=score_payload(components, ("16", "70", "90")))
    assert response.status_code == 200, response.text
    assert Decimal(response.json()["final_score"]) == Decimal("81")
    response = await client.put(url, headers=owner, json=score_payload(components, ("0.01", "0", "0")))
    assert response.status_code == 200, response.text
    assert Decimal(response.json()["final_score"]) == Decimal("0.02")


@pytest.mark.asyncio
@pytest.mark.parametrize("weights,maximums,expected", [
    (("1.21", "48.79", "50"), ("22", "100", "100"), "0.06"),
    (("0.01", "0.01", "99.98"), ("3", "6", "100"), "0.01"),
])
async def test_normalized_contributions_round_exact_half_up(grading_context, weights, maximums, expected):
    client, class_id, enrollments, components, (owner, _, _), _db = grading_context
    payload = [
        {"id": component["id"], "name": component["name"], "category": component["category"],
         "weight": weight, "max_score": maximum}
        for component, weight, maximum in zip(components, weights, maximums)
    ]
    response = await client.put(f"/classes/{class_id}/components", headers=owner, json=payload)
    assert response.status_code == 200, response.text
    values = ("1", "0", "0") if maximums[0] == "22" else ("1", "1", "0")
    response = await client.put(f"/enrollments/{enrollments[0]}/scores", headers=owner,
                                json=score_payload(components, values))
    assert response.status_code == 200, response.text
    assert Decimal(response.json()["final_score"]) == Decimal(expected)


@pytest.mark.asyncio
async def test_score_grade_database_comments(grading_context):
    _client, _class_id, _enrollments, _components, _headers, db = grading_context
    for table, column_count in (("scores", 7), ("grades", 7)):
        result = await db.execute(text("""
            SELECT col_description(c.oid, a.attnum)
            FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_attribute a ON a.attrelid = c.oid
            WHERE n.nspname = 'public' AND c.relname = :table
              AND a.attnum > 0 AND NOT a.attisdropped
        """), {"table": table})
        comments = result.scalars().all()
        assert len(comments) == column_count and all(comments)
        assert await db.scalar(text("SELECT obj_description(to_regclass(:table), 'pg_class')"), {"table": table})


@pytest.mark.asyncio
async def test_component_reweight_recalculates_draft(grading_context):
    client, class_id, enrollments, components, (owner, _, _), _db = grading_context
    url = f"/enrollments/{enrollments[0]}/scores"
    assert (await client.put(url, headers=owner, json=score_payload(components))).status_code == 200
    payload = [
        {key: component[key] for key in ("id", "name", "category", "weight", "max_score", "order_index")}
        for component in components
    ]
    payload[0]["weight"], payload[2]["weight"] = "20", "50"
    response = await client.put(f"/classes/{class_id}/components", headers=owner, json=payload)
    assert response.status_code == 200, response.text
    row = (await client.get(f"/classes/{class_id}/grades", headers=owner)).json()["grades"][0]
    assert Decimal(row["final_score"]) == Decimal("82")
    # Changing a maximum also changes the normalized contribution.
    response = await client.patch(f"/components/{components[0]['id']}", headers=owner,
                                  json={"max_score": "200"})
    assert response.status_code == 200, response.text
    row = (await client.get(f"/classes/{class_id}/grades", headers=owner)).json()["grades"][0]
    assert Decimal(row["final_score"]) == Decimal("74")


@pytest.mark.asyncio
async def test_component_maximum_cannot_invalidate_saved_score(grading_context):
    client, class_id, enrollments, components, (owner, _, _), _db = grading_context
    await client.put(f"/enrollments/{enrollments[0]}/scores", headers=owner, json=score_payload(components))
    response = await client.patch(f"/components/{components[0]['id']}", headers=owner,
                                  json={"max_score": "79"})
    assert response.status_code == 422, response.text
    data = (await client.get(f"/classes/{class_id}/grades", headers=owner)).json()
    assert Decimal(data["components"][0]["max_score"]) == Decimal("100")
    assert Decimal(data["grades"][0]["final_score"]) == Decimal("81")


@pytest.mark.asyncio
async def test_scored_component_removal_rolls_back_entire_configuration(grading_context):
    client, class_id, enrollments, components, (owner, _, _), _db = grading_context
    await client.put(f"/enrollments/{enrollments[0]}/scores", headers=owner, json=score_payload(components))
    payload = [
        {"id": component["id"], "name": component["name"], "category": component["category"], "weight": "50"}
        for component in components[1:]
    ]
    response = await client.put(f"/classes/{class_id}/components", headers=owner, json=payload)
    assert response.status_code == 409, response.text
    data = (await client.get(f"/classes/{class_id}/grades", headers=owner)).json()
    assert data["components"] == components
    assert Decimal(data["grades"][0]["final_score"]) == Decimal("81")


@pytest.mark.asyncio
async def test_finalized_scores_and_components_are_immutable(grading_context):
    from app.models.grade import Grade

    client, class_id, enrollments, components, (owner, _, admin), db = grading_context
    url = f"/enrollments/{enrollments[0]}/scores"
    await client.put(url, headers=owner, json=score_payload(components))
    await db.execute(update(Grade).where(Grade.enrollment_id == uuid.UUID(enrollments[0])).values(
        status="finalized", finalized_at=datetime.now(timezone.utc),
    ))
    await db.commit()
    for headers in (owner, admin):
        assert (await client.put(url, headers=headers, json={components[0]["id"]: "100"})).status_code == 409
        response = await client.patch(f"/components/{components[0]['id']}", headers=headers, json={"name": "X"})
        assert response.status_code == 409, response.text
        response = await client.put(f"/classes/{class_id}/components", headers=headers, json=[
            {"id": component["id"], "name": component["name"], "category": component["category"],
             "weight": component["weight"]} for component in components
        ])
        assert response.status_code == 409, response.text
    row = (await client.get(f"/classes/{class_id}/grades", headers=owner)).json()["grades"][0]
    assert row["status"] == "finalized" and Decimal(row["final_score"]) == Decimal("81")


@pytest.mark.asyncio
async def test_score_failure_rolls_back_scores_and_grade(grading_context, monkeypatch):
    from sqlalchemy.exc import IntegrityError
    from app.repositories import grades as grade_repo

    client, class_id, enrollments, components, (owner, _, _), _db = grading_context

    def fail_grade_insert(*args, **kwargs):
        raise IntegrityError("INSERT grades", {}, Exception("simulated conflict"))

    monkeypatch.setattr(grade_repo, "add_draft", fail_grade_insert)
    response = await client.put(f"/enrollments/{enrollments[0]}/scores", headers=owner, json=score_payload(components))
    assert response.status_code == 409, response.text
    row = (await client.get(f"/classes/{class_id}/grades", headers=owner)).json()["grades"][0]
    assert row["scores"] == {} and row["final_score"] is None


@pytest.mark.asyncio
async def test_scores_recheck_class_owner_after_lock(grading_context, monkeypatch):
    from app.repositories import component as component_repo

    client, class_id, enrollments, components, (owner, other, _), db = grading_context
    original_lock = component_repo.lock_class
    other_id = uuid.UUID(decode_token(other["Authorization"].split()[1])["sub"])

    async def reassign_before_lock(session, target_id):
        await db.execute(update(Class).where(Class.id == target_id).values(lecturer_id=other_id)
                         .execution_options(synchronize_session=False))
        await original_lock(session, target_id)

    monkeypatch.setattr(component_repo, "lock_class", reassign_before_lock)
    response = await client.put(f"/enrollments/{enrollments[0]}/scores", headers=owner, json=score_payload(components))
    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_enrollment_removed_before_lock_returns_not_found(grading_context, monkeypatch):
    from sqlalchemy import delete
    from app.repositories import component as component_repo

    client, _class_id, enrollments, components, (owner, _, _), db = grading_context
    original_lock = component_repo.lock_class

    async def delete_before_lock(session, target_id):
        await db.execute(delete(Enrollment).where(Enrollment.id == uuid.UUID(enrollments[0]))
                         .execution_options(synchronize_session=False))
        await original_lock(session, target_id)

    monkeypatch.setattr(component_repo, "lock_class", delete_before_lock)
    response = await client.put(f"/enrollments/{enrollments[0]}/scores", headers=owner, json=score_payload(components))
    assert response.status_code == 404, response.text


@pytest.mark.asyncio
async def test_concurrent_writers_keep_last_score_and_recompute_final(monkeypatch):
    from sqlalchemy import delete
    from app.database import AsyncSessionLocal
    from app.models.component import Component
    from app.models.grade import Grade
    from app.models.score import Score
    from app.repositories import component as component_repo

    # Use committed, uniquely identified data so separate request connections can see it.
    suffix = uuid.uuid4().hex
    owner_id, admin_id, course_id, class_id, student_id, enrollment_id = [uuid.uuid4() for _ in range(6)]
    component_ids = [uuid.uuid4() for _ in range(3)]
    try:
        async with AsyncSessionLocal() as db:
            db.add_all([
                User(id=owner_id, email=f"concurrent-owner-{suffix}@example.com", role="lecturer",
                     full_name="Dosen", password_hash="unused"),
                User(id=admin_id, email=f"concurrent-admin-{suffix}@example.com", role="superadmin",
                     full_name="Admin", password_hash="unused"),
            ])
            await db.flush()
            db.add(Course(id=course_id, code=f"CON-{suffix}", name="Serentak", credits=3,
                          semester="2026/1", created_by=owner_id))
            await db.flush()
            db.add(Class(id=class_id, course_id=course_id, lecturer_id=owner_id, section="A", academic_year="2026/2027"))
            db.add(Student(id=student_id, nim=f"CON-{suffix}", full_name="Mahasiswa"))
            await db.flush()
            db.add(Enrollment(id=enrollment_id, class_id=class_id, student_id=student_id))
            db.add_all([
                Component(id=component_id, class_id=class_id, name=category, category=category,
                          weight=weight, max_score=100)
                for component_id, category, weight in zip(component_ids, ("tugas", "uts", "uas"), (30, 30, 40))
            ])
            await db.commit()

        original_lock = component_repo.lock_class
        first_locked, second_started = asyncio.Event(), asyncio.Event()
        call_count = 0

        async def ordered_lock(db, target_id):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                await original_lock(db, target_id)
                first_locked.set()
                await second_started.wait()
            else:
                second_started.set()
                await original_lock(db, target_id)

        monkeypatch.setattr(component_repo, "lock_class", ordered_lock)
        owner = {"Authorization": "Bearer " + create_access_token(str(owner_id), "lecturer")}
        admin = {"Authorization": "Bearer " + create_access_token(str(admin_id), "superadmin")}
        url = f"/enrollments/{enrollment_id}/scores"
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            first_task = asyncio.create_task(client.put(url, headers=owner, json={
                str(component_id): value for component_id, value in zip(component_ids, (80, 70, 90))
            }))
            await asyncio.wait_for(first_locked.wait(), timeout=10)
            first, second = await asyncio.wait_for(asyncio.gather(
                first_task, client.put(url, headers=admin, json={str(component_ids[0]): 100}),
            ), timeout=10)
            assert first.status_code == second.status_code == 200, (first.text, second.text)
            assert first.json()["id"] == second.json()["id"]
            data = (await client.get(f"/classes/{class_id}/grades", headers=owner)).json()
            assert Decimal(data["grades"][0]["final_score"]) == Decimal("87")
            assert Decimal(data["grades"][0]["scores"][str(component_ids[0])]) == Decimal("100")
        async with AsyncSessionLocal() as db:
            rows = (await db.execute(text(
                "SELECT entered_by, entered_at, updated_at FROM scores "
                "WHERE enrollment_id = :id AND component_id = :component"
            ), {"id": enrollment_id, "component": component_ids[0]})).all()
            assert len(rows) == 1 and rows[0].entered_by == admin_id
            assert rows[0].updated_at > rows[0].entered_at
    finally:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(Score).where(Score.enrollment_id == enrollment_id))
            await db.execute(delete(Grade).where(Grade.enrollment_id == enrollment_id))
            await db.execute(delete(Component).where(Component.class_id == class_id))
            await db.execute(delete(Enrollment).where(Enrollment.class_id == class_id))
            await db.execute(delete(Class).where(Class.id == class_id))
            await db.execute(delete(Course).where(Course.id == course_id))
            await db.execute(delete(Student).where(Student.id == student_id))
            await db.execute(delete(User).where(User.id.in_([owner_id, admin_id])))
            await db.commit()
