"""Tests for course CRUD and lecturer access scoping.

CRUD mata kuliah dan cakupan pemilik.

Memerlukan PostgreSQL disposable yang dimigrasi; beberapa skenario
melakukan commit nyata.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import delete

from app.database import AsyncSessionLocal
from app.main import app
from app.models.course import Course
from app.models.user import User


async def _login(client: AsyncClient, email: str, password: str) -> str:
    """Login melalui API untuk mendapat token skenario."""
    r = await client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    """Bentuk header bearer dari token skenario."""
    return {"Authorization": f"Bearer {token}"}


async def _cleanup(course_ids: list[str], user_emails: list[str]) -> None:
    """Hapus data skenario sesuai urutan relasi."""
    async with AsyncSessionLocal() as session:
        if course_ids:
            await session.execute(
                delete(Course).where(Course.id.in_([uuid.UUID(cid) for cid in course_ids]))
            )
        if user_emails:
            await session.execute(delete(User).where(User.email.in_(user_emails)))
        await session.commit()


@pytest.mark.asyncio
async def test_course_crud_as_superadmin():
    """Uji persistence, konflik, dan proteksi hapus admin."""
    suffix = uuid.uuid4().hex[:8]
    code = f"IF{suffix}".upper()
    other_code = f"SI{suffix}".upper()
    course_ids: list[str] = []

    async with AsyncClient(app=app, base_url="http://test") as c:
        token = await _login(c, "admin@example.com", "admin123")
        headers = _headers(token)
        me = await c.get("/auth/me", headers=headers)
        assert me.status_code == 200, me.text
        admin_id = me.json()["id"]

        # Create
        payload = {
            "code": code,
            "name": "Pemrograman Web",
            "credits": 3,
            "semester": "2026/1",
        }
        r = await c.post("/courses", headers=headers, json=payload)
        assert r.status_code == 201, r.text
        created = r.json()
        course_ids.append(created["id"])
        assert created["code"] == code
        assert created["name"] == "Pemrograman Web"
        assert created["credits"] == 3
        assert created["semester"] == "2026/1"
        assert created["created_by"] == admin_id
        assert created["created_at"]

        # Duplicate code -> 409
        r = await c.post("/courses", headers=headers, json={**payload, "name": "Duplikat"})
        assert r.status_code == 409, r.text

        # List contains the new course
        r = await c.get("/courses", headers=headers)
        assert r.status_code == 200, r.text
        assert created["id"] in [course["id"] for course in r.json()]

        # Get
        r = await c.get(f"/courses/{created['id']}", headers=headers)
        assert r.status_code == 200, r.text
        assert r.json()["code"] == code

        # Second course, used to verify duplicate code on update
        r = await c.post(
            "/courses",
            headers=headers,
            json={
                "code": other_code,
                "name": "Sistem Informasi",
                "credits": 3,
                "semester": "2026/1",
            },
        )
        assert r.status_code == 201, r.text
        other_id = r.json()["id"]
        course_ids.append(other_id)

        # Update
        r = await c.patch(
            f"/courses/{created['id']}",
            headers=headers,
            json={"name": "Pemrograman Web Lanjut", "credits": 4},
        )
        assert r.status_code == 200, r.text
        updated = r.json()
        assert updated["name"] == "Pemrograman Web Lanjut"
        assert updated["credits"] == 4
        assert updated["code"] == code

        # Updating to an existing code -> 409
        r = await c.patch(
            f"/courses/{created['id']}",
            headers=headers,
            json={"code": other_code},
        )
        assert r.status_code == 409, r.text

        # Delete
        r = await c.delete(f"/courses/{created['id']}", headers=headers)
        assert r.status_code == 204, r.text
        r = await c.get(f"/courses/{created['id']}", headers=headers)
        assert r.status_code == 404

    await _cleanup(course_ids, [])


@pytest.mark.asyncio
async def test_lecturer_course_access_scoping():
    """Isolasi akses mata kuliah berdasarkan kepemilikan."""
    suffix = uuid.uuid4().hex[:8]
    email1 = f"dosen1-{suffix}@example.com"
    email2 = f"dosen2-{suffix}@example.com"
    code = f"MK{suffix}".upper()
    course_ids: list[str] = []
    user_emails = [email1, email2]

    async with AsyncClient(app=app, base_url="http://test") as c:
        admin_token = await _login(c, "admin@example.com", "admin123")
        admin_headers = _headers(admin_token)

        # Create two lecturers via the admin API
        r = await c.post(
            "/admin/users",
            headers=admin_headers,
            json={
                "email": email1,
                "password": "rahasia123",
                "full_name": "Dosen Satu",
                "role": "lecturer",
            },
        )
        assert r.status_code == 201, r.text
        lecturer1_id = r.json()["id"]

        r = await c.post(
            "/admin/users",
            headers=admin_headers,
            json={
                "email": email2,
                "password": "rahasia123",
                "full_name": "Dosen Dua",
                "role": "lecturer",
            },
        )
        assert r.status_code == 201, r.text

        token1 = await _login(c, email1, "rahasia123")
        token2 = await _login(c, email2, "rahasia123")
        headers1 = _headers(token1)
        headers2 = _headers(token2)

        # Lecturer 1 creates a course
        payload = {
            "code": code,
            "name": "Basis Data",
            "credits": 3,
            "semester": "2026/1",
        }
        r = await c.post("/courses", headers=headers1, json=payload)
        assert r.status_code == 201, r.text
        created = r.json()
        course_id = created["id"]
        course_ids.append(course_id)
        assert created["created_by"] == lecturer1_id

        # Lecturer 1 sees own course
        r = await c.get("/courses", headers=headers1)
        assert r.status_code == 200, r.text
        assert course_id in [course["id"] for course in r.json()]

        # Lecturer 2 does not see it in the list
        r = await c.get("/courses", headers=headers2)
        assert r.status_code == 200, r.text
        assert course_id not in [course["id"] for course in r.json()]

        # Lecturer 2 cannot read, update, or delete another lecturer's course
        r = await c.get(f"/courses/{course_id}", headers=headers2)
        assert r.status_code == 403, r.text
        r = await c.patch(f"/courses/{course_id}", headers=headers2, json={"name": "Diubah"})
        assert r.status_code == 403, r.text
        r = await c.delete(f"/courses/{course_id}", headers=headers2)
        assert r.status_code == 403, r.text

        # The course is unchanged
        r = await c.get(f"/courses/{course_id}", headers=headers1)
        assert r.status_code == 200, r.text
        assert r.json()["name"] == "Basis Data"

        # Code is unique across all courses, even for another lecturer
        r = await c.post("/courses", headers=headers2, json=payload)
        assert r.status_code == 409, r.text

        # Superadmin sees and can manage all courses
        r = await c.get("/courses", headers=admin_headers)
        assert r.status_code == 200, r.text
        assert course_id in [course["id"] for course in r.json()]

        r = await c.patch(
            f"/courses/{course_id}",
            headers=admin_headers,
            json={"credits": 4},
        )
        assert r.status_code == 200, r.text
        assert r.json()["credits"] == 4

        # Lecturer 1 can still update their own course
        r = await c.patch(
            f"/courses/{course_id}",
            headers=headers1,
            json={"semester": "2026/2"},
        )
        assert r.status_code == 200, r.text
        assert r.json()["semester"] == "2026/2"

    await _cleanup(course_ids, user_emails)


@pytest.mark.asyncio
async def test_courses_require_authentication():
    """Tolak akses mata kuliah tanpa sesi."""
    async with AsyncClient(app=app, base_url="http://test") as c:
        r = await c.get("/courses")
        assert r.status_code == 401
