"""Read-only finalized history and per-lecturer visibility."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import delete, event, select, update

from app.database import engine
from app.models.class_ import Class
from app.models.component import Component
from app.models.enrollment import Enrollment
from app.models.grade import Grade
from app.models.ranking import Ranking
from app.models.student import Student
from app.services.auth import decode_token
from tests.test_finalization import fill_scores, mock_publisher
from tests.test_scores import grading_context, score_payload


@pytest_asyncio.fixture(loop_scope="session")
async def history_context(grading_context, monkeypatch):
    client, original_class, enrollments, components, (owner, other, admin), db = grading_context
    mock_publisher(monkeypatch)
    await fill_scores(grading_context)
    response = await client.post(f"/classes/{original_class}/finalize", headers=owner)
    assert response.status_code == 202, response.text
    enrollment = await db.get(Enrollment, uuid.UUID(enrollments[0]))
    student = await db.get(Student, enrollment.student_id)
    student_id, nim = str(student.id), student.nim
    history_classes = [original_class]
    history_enrollments = [enrollments[0]]
    all_components = [components]
    other_id = decode_token(other["Authorization"].split()[1])["sub"]
    for index, headers in enumerate((owner, other, owner), start=1):
        response = await client.post("/courses", headers=admin, json={
            "code": f"HIS-{uuid.uuid4().hex}", "name": f"Riwayat {index}", "credits": 3,
            "semester": f"2026/{index + 1}",
        })
        assert response.status_code == 201, response.text
        course_id = response.json()["id"]
        lecturer_id = other_id if index == 2 else decode_token(owner["Authorization"].split()[1])["sub"]
        response = await client.post("/classes", headers=admin, json={
            "course_id": course_id, "lecturer_id": lecturer_id, "section": "A", "academic_year": "2026/2027",
        })
        assert response.status_code == 201, response.text
        class_id = response.json()["id"]
        response = await client.post(f"/classes/{class_id}/enrollments", headers=headers, json={"nim": nim})
        assert response.status_code == 201, response.text
        enrollment_id = response.json()["id"]
        response = await client.post(f"/classes/{class_id}/components", headers=headers, json=[
            {"name": "Tugas", "category": "tugas", "weight": "30", "order_index": 2},
            {"name": "UTS", "category": "uts", "weight": "30", "order_index": 0},
            {"name": "UAS", "category": "uas", "weight": "40", "order_index": 1},
        ])
        assert response.status_code == 201, response.text
        current_components = response.json()
        response = await client.put(f"/enrollments/{enrollment_id}/scores", headers=headers,
                                    json=score_payload(current_components, ("0", "100", "100")))
        assert response.status_code == 200, response.text
        if index < 3:
            response = await client.post(f"/classes/{class_id}/finalize", headers=headers)
            assert response.status_code == 202, response.text
        history_classes.append(class_id)
        history_enrollments.append(enrollment_id)
        all_components.append(current_components)
    for index, enrollment_id in enumerate(history_enrollments[:3]):
        await db.execute(update(Grade).where(Grade.enrollment_id == uuid.UUID(enrollment_id))
                         .values(finalized_at=datetime(2026, index + 1, 1, tzinfo=timezone.utc)))
    await db.commit()
    return grading_context, student_id, history_classes, history_enrollments, all_components


@pytest.mark.asyncio
async def test_history_returns_finalized_grades_and_component_scores(history_context):
    context, student_id, class_ids, enrollments, component_sets = history_context
    client, _class_id, _enrollments, _components, (owner, _other, admin), db = context
    response = await client.get(f"/students/{student_id}/history", headers=owner)
    assert response.status_code == 200, response.text
    rows = response.json()
    assert [row["enrollment_id"] for row in rows] == [enrollments[1], enrollments[0]]
    assert [row["course"]["semester"] for row in rows] == ["2026/2", "2026/1"]
    assert [Decimal(row["final_score"]) for row in rows] == [Decimal("70"), Decimal("81")]
    assert rows[0]["class"] == {"id": class_ids[1], "section": "A", "academic_year": "2026/2027"}
    assert rows[0]["course"]["credits"] == 3 and rows[0]["course"]["name"] == "Riwayat 1"
    assert rows[0]["course"]["id"] and rows[0]["course"]["code"]
    assert rows[0]["rank"] == 1 and rows[1]["rank"] == 1
    assert rows[0]["finalized_at"] == "2026-02-01T00:00:00Z"
    ordered = sorted(component_sets[1], key=lambda row: row["order_index"])
    assert [row["id"] for row in rows[0]["components"]] == [row["id"] for row in ordered]
    for component in rows[0]["components"]:
        original = next(row for row in component_sets[1] if row["id"] == component["id"])
        for key in ("name", "category", "order_index"):
            assert component[key] == original[key]
        assert Decimal(component["weight"]) == Decimal(original["weight"])
        assert Decimal(component["max_score"]) == Decimal("100")
        assert Decimal(component["score"]) == (Decimal("0") if component["category"] == "tugas" else Decimal("100"))
    grades = (await db.execute(select(Grade).where(Grade.enrollment_id.in_(
        [uuid.UUID(value) for value in enrollments[:2]]
    )))).scalars().all()
    assert {row["grade_id"] for row in rows} == {str(grade.id) for grade in grades}
    rows = (await client.get(f"/students/{student_id}/history", headers=admin)).json()
    assert [row["enrollment_id"] for row in rows] == list(reversed(enrollments[:3]))
    assert enrollments[3] not in {row["enrollment_id"] for row in rows}


@pytest.mark.asyncio
async def test_history_scopes_components_and_grades_to_current_lecturer(history_context):
    context, student_id, class_ids, enrollments, components = history_context
    client, _class_id, _enrollments, _components, (owner, other, _admin), db = context
    rows = (await client.get(f"/students/{student_id}/history", headers=other)).json()
    assert [row["enrollment_id"] for row in rows] == [enrollments[2]]
    assert {row["id"] for row in rows[0]["components"]} == {row["id"] for row in components[2]}
    # Reassignment follows existing class access rules.
    other_id = uuid.UUID(decode_token(other["Authorization"].split()[1])["sub"])
    await db.execute(update(Class).where(Class.id == uuid.UUID(class_ids[0])).values(lecturer_id=other_id))
    await db.commit()
    assert len((await client.get(f"/students/{student_id}/history", headers=owner)).json()) == 1
    assert len((await client.get(f"/students/{student_id}/history", headers=other)).json()) == 2


@pytest.mark.asyncio
async def test_history_keeps_grade_when_ranking_is_missing(history_context):
    context, student_id, _classes, enrollments, _components = history_context
    client, _class_id, _enrollments, _components, (owner, _, _), db = context
    await db.execute(delete(Ranking).where(Ranking.enrollment_id == uuid.UUID(enrollments[0])))
    await db.commit()
    rows = (await client.get(f"/students/{student_id}/history", headers=owner)).json()
    assert len(rows) == 2 and rows[1]["rank"] is None


@pytest.mark.asyncio
async def test_history_empty_and_request_errors(grading_context):
    client, _class_id, enrollments, components, (owner, other, _), db = grading_context
    enrollment = await db.get(Enrollment, uuid.UUID(enrollments[0]))
    url = f"/students/{enrollment.student_id}/history"
    assert (await client.get(url)).status_code == 401
    assert (await client.get(url, headers=owner)).json() == []
    assert (await client.get(url, headers=other)).json() == []
    await client.put(f"/enrollments/{enrollments[0]}/scores", headers=owner, json=score_payload(components))
    assert (await client.get(url, headers=owner)).json() == []
    assert (await client.get(f"/students/{uuid.uuid4()}/history", headers=owner)).status_code == 404
    assert (await client.get("/students/invalid/history", headers=owner)).status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
async def test_history_rejects_write_methods(history_context, method):
    context, student_id, _classes, _enrollments, _components = history_context
    client, _class_id, _ids, _rows, (owner, _, _), _db = context
    response = await client.request(method, f"/students/{student_id}/history", headers=owner)
    assert response.status_code == 405, response.text


@pytest.mark.asyncio
async def test_history_reads_are_batched_and_do_not_write(history_context):
    context, student_id, _classes, _enrollments, _components = history_context
    client, _class_id, _ids, _rows, (_, _, admin), _db = context
    statements = []

    def record(_conn, _cursor, statement, _parameters, _execution_context, _executemany):
        statements.append(statement)

    event.listen(engine.sync_engine, "before_cursor_execute", record)
    try:
        response = await client.get(f"/students/{student_id}/history", headers=admin)
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", record)
    assert response.status_code == 200, response.text
    assert len(response.json()) == 3
    # The fixture starts a savepoint when the request first uses its shared connection.
    queries = [statement for statement in statements if not statement.lstrip().upper().startswith("SAVEPOINT ")]
    assert 1 <= len(queries) <= 4  # Authentication plus at most three history queries.
    assert all(statement.lstrip().upper().startswith("SELECT") for statement in queries)


@pytest.mark.asyncio
async def test_rejected_release_edits_leave_history_unchanged(history_context):
    context, student_id, classes, enrollments, components = history_context
    client, _class_id, _ids, _rows, (owner, _, _), _db = context
    url = f"/students/{student_id}/history"
    before = (await client.get(url, headers=owner)).json()
    assert (await client.put(f"/enrollments/{enrollments[0]}/scores", headers=owner,
                             json={components[0][0]["id"]: "100"})).status_code == 409
    assert (await client.patch(f"/components/{components[0][0]['id']}", headers=owner,
                               json={"name": "Ubah"})).status_code == 409
    assert (await client.delete(f"/classes/{classes[0]}/enrollments/{enrollments[0]}", headers=owner)).status_code == 409
    assert (await client.get(url, headers=owner)).json() == before


@pytest.mark.asyncio
async def test_history_breaks_timestamp_and_component_order_ties_deterministically(history_context):
    context, student_id, classes, enrollments, _components = history_context
    client, _class_id, _ids, _rows, (_, _, admin), db = context
    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)
    await db.execute(update(Grade).where(Grade.enrollment_id.in_([uuid.UUID(value) for value in enrollments[:3]]))
                     .values(finalized_at=timestamp))
    await db.execute(update(Component).where(Component.class_id.in_([uuid.UUID(value) for value in classes[:3]]))
                     .values(order_index=0, created_at=timestamp))
    await db.commit()
    rows = (await client.get(f"/students/{student_id}/history", headers=admin)).json()
    assert [row["enrollment_id"] for row in rows] == sorted(enrollments[:3])
    for row in rows:
        assert [component["id"] for component in row["components"]] == sorted(component["id"] for component in row["components"])
