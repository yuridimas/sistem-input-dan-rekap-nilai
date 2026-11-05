"""Dashboard visibility, class release semantics, and batched reads.

Agregasi dashboard berdasarkan penugasan dan rilis.

Memerlukan PostgreSQL disposable yang dimigrasi; beberapa skenario
melakukan commit nyata.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine, get_db
from app.main import app
from app.models.class_ import Class
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.grade import Grade
from app.models.student import Student
from app.models.user import User
from app.services.auth import create_access_token


@pytest_asyncio.fixture(loop_scope="session")
async def dashboard_context():
    """Siapkan variasi pemilik dan status kelas."""
    async with engine.connect() as connection:
        transaction = await connection.begin()
        try:
            async with AsyncSession(bind=connection, expire_on_commit=False,
                                    join_transaction_mode="create_savepoint") as db:
                suffix = uuid.uuid4().hex
                users = [User(email=f"dashboard-{i}-{suffix}@example.com", password_hash="unused",
                              full_name=f"User {i}", role=role, is_active=i != 4)
                         for i, role in enumerate(["lecturer", "lecturer", "superadmin",
                                                   "lecturer", "lecturer", "unsupported"])]
                db.add_all(users)
                await db.flush()
                courses = [Course(code=f"DASH-{i}-{suffix}", name=f"Course {i}", credits=3,
                                  semester="2026/1", created_by=users[0 if i == 2 else 2].id,
                                  created_at=datetime(2026, 10, i + 1, tzinfo=timezone.utc))
                           for i in range(3)]
                db.add_all(courses)
                await db.flush()

                async def add_class(course, lecturer, section, statuses, released_at=None):
                    """Siapkan variasi kelas pending dan released."""
                    class_ = Class(course_id=course.id, lecturer_id=lecturer.id,
                                   section=section, academic_year="2026/2027")
                    db.add(class_)
                    await db.flush()
                    for index, grade_status in enumerate(statuses):
                        student = Student(nim=f"{uuid.uuid4().hex}", full_name=f"Student {index}")
                        db.add(student)
                        await db.flush()
                        enrollment = Enrollment(class_id=class_.id, student_id=student.id)
                        db.add(enrollment)
                        await db.flush()
                        if grade_status is not None:
                            db.add(Grade(enrollment_id=enrollment.id, final_score=80,
                                         status=grade_status,
                                         finalized_at=released_at if grade_status == "finalized" else None))
                    await db.flush()
                    return class_

                released_at = datetime(2026, 10, 20, tzinfo=timezone.utc)
                classes = [
                    await add_class(courses[0], users[0], "A", []),
                    await add_class(courses[0], users[1], "B", ["finalized"], released_at),
                    await add_class(courses[1], users[0], "A", [None, None]),
                    await add_class(courses[1], users[0], "B", ["draft", "draft"]),
                    await add_class(courses[1], users[0], "C", ["finalized", "draft"], released_at),
                    await add_class(courses[1], users[0], "D", ["finalized", "finalized"], released_at),
                ]
                headers = [{"Authorization": f"Bearer {create_access_token(str(user.id), user.role)}"}
                           for user in users]

                async def override_db():
                    """Pinjamkan session fixture ke dependency endpoint.
                    """
                    yield db

                app.dependency_overrides[get_db] = override_db
                try:
                    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                        yield client, db, users, courses, classes, headers, add_class
                finally:
                    app.dependency_overrides.pop(get_db, None)
        finally:
            await transaction.rollback()


@pytest.mark.asyncio
async def test_dashboard_lecturer_counts_assigned_not_created_courses(dashboard_context):
    """Hitung penugasan dosen tanpa bergantung pencipta."""
    client, _, _, courses, classes, headers, _ = dashboard_context
    response = await client.get("/dashboard/summary", headers=headers[0])
    assert response.status_code == 200, response.text
    data = response.json()
    assert (data["course_count"], data["class_count"], data["pending_class_count"]) == (2, 5, 4)
    expected_courses = sorted(courses[:2], key=lambda course: course.created_at, reverse=True)
    assert [course["id"] for course in data["courses"]] == [str(course.id) for course in expected_courses]
    assert datetime.fromisoformat(data["courses"][0]["created_at"]) == courses[1].created_at
    rows = {row["id"]: row for course in data["courses"] for row in course["classes"]}
    assert str(classes[1].id) not in rows
    assert [rows[str(classes[i].id)]["status"] for i in (0, 2, 3, 4, 5)] == ["pending"] * 4 + ["released"]
    assert rows[str(classes[0].id)]["student_count"] == 0
    assert rows[str(classes[4].id)]["released_at"] is None
    assert rows[str(classes[5].id)]["student_count"] == 2
    assert rows[str(classes[5].id)]["released_at"] == "2026-10-20T00:00:00Z"
    assert [row["id"] for row in data["recently_released"]] == [str(classes[5].id)]
    assert data["recently_released"][0]["course_id"] == str(courses[1].id)


@pytest.mark.asyncio
async def test_dashboard_admin_includes_unassigned_courses_and_other_lecturers(dashboard_context):
    """Sertakan kelas lintas dosen dan mata kuliah tanpa kelas."""
    client, _, _, courses, classes, headers, _ = dashboard_context
    data = (await client.get("/dashboard/summary", headers=headers[2])).json()
    assert (data["course_count"], data["class_count"], data["pending_class_count"]) == (3, 6, 4)
    assert next(course for course in data["courses"] if course["id"] == str(courses[2].id))["classes"] == []
    other = (await client.get("/dashboard/summary", headers=headers[1])).json()
    assert (other["course_count"], other["class_count"], other["pending_class_count"]) == (1, 1, 0)
    assert other["courses"][0]["classes"][0]["id"] == str(classes[1].id)


@pytest.mark.asyncio
async def test_dashboard_empty_account(dashboard_context):
    """Kembalikan hasil kosong untuk akun tanpa penugasan."""
    client, _, _, _, _, headers, _ = dashboard_context
    response = await client.get("/dashboard/summary", headers=headers[3])
    assert response.status_code == 200
    assert response.json() == {"course_count": 0, "class_count": 0, "pending_class_count": 0,
                               "courses": [], "recently_released": []}


@pytest.mark.asyncio
async def test_dashboard_orders_courses_by_creation_time(dashboard_context):
    """Expose mata kuliah terbaru pertama agar dashboard dapat membatasi preview."""
    client, db, users, _, _, headers, add_class = dashboard_context
    suffix = uuid.uuid4().hex
    courses = [Course(code=f"RECENT-{index}-{suffix}", name=f"Recent {index}", credits=3,
                      semester="2030/1", created_by=users[0].id,
                      created_at=datetime(2030, 1, 1, tzinfo=timezone.utc) + timedelta(days=index))
               for index in range(7)]
    db.add_all(courses)
    await db.flush()
    for index, course in enumerate(courses):
        await add_class(course, users[0], f"R{index}", [None])

    response = await client.get("/dashboard/summary", headers=headers[0])
    assert response.status_code == 200, response.text
    data = response.json()
    recent_ids = [row["id"] for row in data["courses"] if row["id"] in {str(course.id) for course in courses}]
    assert recent_ids == [str(course.id) for course in reversed(courses)]
    assert all("created_at" in row for row in data["courses"])


@pytest.mark.asyncio
@pytest.mark.parametrize("user_index,expected", [(None, 401), (4, 401), (5, 403)])
async def test_dashboard_requires_active_supported_role(dashboard_context, user_index, expected):
    """Tolak akun nonaktif dan role yang tak didukung."""
    client, _, _, _, _, headers, _ = dashboard_context
    response = await client.get("/dashboard/summary", headers={} if user_index is None else headers[user_index])
    assert response.status_code == expected


@pytest.mark.asyncio
async def test_dashboard_recent_release_limit_and_deterministic_order(dashboard_context):
    """Batasi lima rilis dengan tie-break deterministik."""
    client, _, users, courses, _, headers, add_class = dashboard_context
    newest = datetime(2026, 10, 25, tzinfo=timezone.utc)
    added = [await add_class(courses[0], users[0], f"R{i}", ["finalized"], newest - timedelta(days=i // 2))
             for i in range(7)]
    data = (await client.get("/dashboard/summary", headers=headers[0])).json()
    # Explicitly sort by release date descending, then ID ascending.
    expected = sorted(added, key=lambda row: (int(row.section[1:]) // 2, str(row.id)))[:5]
    assert [row["id"] for row in data["recently_released"]] == [str(row.id) for row in expected]


@pytest.mark.asyncio
async def test_dashboard_reads_in_constant_queries_without_writes(dashboard_context):
    """Biaya query harus konstan dan GET tidak boleh menulis data."""
    client, _, users, courses, _, headers, add_class = dashboard_context
    statements = []

    def record(_conn, _cursor, statement, _parameters, _context, _executemany):
        """Catat statement untuk uji anggaran query."""
        statements.append(statement)

    event.listen(engine.sync_engine, "before_cursor_execute", record)
    try:
        assert (await client.get("/dashboard/summary", headers=headers[0])).status_code == 200
        baseline = len(statements)
        for i in range(8):
            await add_class(courses[0], users[0], f"Q{i}", [None] * 3)
        statements.clear()
        assert (await client.get("/dashboard/summary", headers=headers[0])).status_code == 200
        assert len(statements) == baseline <= 4
        assert all(statement.lstrip().upper().startswith("SELECT") for statement in statements)
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", record)
