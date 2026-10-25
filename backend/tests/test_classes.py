"""Tests for classes, enrollments, roster, and lecturer access scoping."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import delete

from app.database import AsyncSessionLocal
from app.main import app
from app.models.class_ import Class
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.student import Student
from app.models.user import User


async def _login(client: AsyncClient, email: str, password: str) -> str:
    r = await client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _cleanup(
    class_ids: list[str],
    course_ids: list[str],
    nims: list[str],
    user_emails: list[str],
) -> None:
    async with AsyncSessionLocal() as session:
        if class_ids:
            class_uuids = [uuid.UUID(cid) for cid in class_ids]
            await session.execute(
                delete(Enrollment).where(Enrollment.class_id.in_(class_uuids))
            )
            await session.execute(delete(Class).where(Class.id.in_(class_uuids)))
        if nims:
            await session.execute(delete(Student).where(Student.nim.in_(nims)))
        if course_ids:
            await session.execute(
                delete(Course).where(
                    Course.id.in_([uuid.UUID(cid) for cid in course_ids])
                )
            )
        if user_emails:
            await session.execute(delete(User).where(User.email.in_(user_emails)))
        await session.commit()


async def _create_lecturer(
    client: AsyncClient, headers: dict[str, str], email: str, name: str
) -> str:
    r = await client.post(
        "/admin/users",
        headers=headers,
        json={
            "email": email,
            "password": "rahasia123",
            "full_name": name,
            "role": "lecturer",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _create_course(
    client: AsyncClient, headers: dict[str, str], code: str
) -> str:
    r = await client.post(
        "/courses",
        headers=headers,
        json={
            "code": code,
            "name": "Pemrograman Web",
            "credits": 3,
            "semester": "2026/1",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


@pytest.mark.asyncio
async def test_class_enrollment_roster_and_delete_flow():
    suffix = uuid.uuid4().hex[:8]
    lecturer_email = f"dosen-kelas-{suffix}@example.com"
    course_code = f"KLS{suffix}".upper()
    nim = f"NIM{suffix}".upper()
    nim2 = f"NIM2{suffix}".upper()
    class_ids: list[str] = []
    course_ids: list[str] = []
    nims = [nim, nim2]

    async with AsyncClient(app=app, base_url="http://test") as c:
        admin_token = await _login(c, "admin@example.com", "admin123")
        admin_headers = _headers(admin_token)
        lecturer_id = await _create_lecturer(
            c, admin_headers, lecturer_email, "Dosen Kelas"
        )
        course_id = await _create_course(c, admin_headers, course_code)
        course_ids.append(course_id)

        lecturer_token = await _login(c, lecturer_email, "rahasia123")
        headers = _headers(lecturer_token)

        # Create class as lecturer -> lecturer_id is the current user
        r = await c.post(
            "/classes",
            headers=headers,
            json={
                "course_id": course_id,
                "section": "A",
                "academic_year": "2026/2027",
            },
        )
        assert r.status_code == 201, r.text
        class_a = r.json()
        class_ids.append(class_a["id"])
        assert class_a["course_id"] == course_id
        assert class_a["section"] == "A"
        assert class_a["academic_year"] == "2026/2027"
        assert class_a["lecturer_id"] == lecturer_id

        # Duplicate (course_id, section, academic_year) -> 409
        r = await c.post(
            "/classes",
            headers=headers,
            json={
                "course_id": course_id,
                "section": "A",
                "academic_year": "2026/2027",
            },
        )
        assert r.status_code == 409, r.text

        # Second class (section B) for the same course
        r = await c.post(
            "/classes",
            headers=headers,
            json={
                "course_id": course_id,
                "section": "B",
                "academic_year": "2026/2027",
            },
        )
        assert r.status_code == 201, r.text
        class_b = r.json()
        class_ids.append(class_b["id"])

        # List contains own classes
        r = await c.get("/classes", headers=headers)
        assert r.status_code == 200, r.text
        listed_ids = [item["id"] for item in r.json()]
        assert class_a["id"] in listed_ids
        assert class_b["id"] in listed_ids

        # Enroll a brand-new student by NIM (student is created)
        r = await c.post(
            f"/classes/{class_a['id']}/enrollments",
            headers=headers,
            json={
                "nim": nim,
                "full_name": "Budi Santoso",
                "email": f"budi-{suffix}@example.com",
            },
        )
        assert r.status_code == 201, r.text
        enrollment_a = r.json()
        assert enrollment_a["id"]
        assert enrollment_a["enrolled_at"]
        assert enrollment_a["student"]["nim"] == nim
        assert enrollment_a["student"]["full_name"] == "Budi Santoso"
        assert enrollment_a["student"]["email"] == f"budi-{suffix}@example.com"

        # Duplicate enrollment in the same class -> 409
        r = await c.post(
            f"/classes/{class_a['id']}/enrollments",
            headers=headers,
            json={"nim": nim},
        )
        assert r.status_code == 409, r.text

        # Enroll the existing student into the second class (no new student)
        r = await c.post(
            f"/classes/{class_b['id']}/enrollments",
            headers=headers,
            json={"nim": nim},
        )
        assert r.status_code == 201, r.text
        enrollment_b = r.json()
        assert enrollment_b["student"]["id"] == enrollment_a["student"]["id"]
        assert enrollment_b["student"]["full_name"] == "Budi Santoso"

        # Roster returns enrollment + student data
        r = await c.get(f"/classes/{class_a['id']}/roster", headers=headers)
        assert r.status_code == 200, r.text
        roster = r.json()
        assert len(roster) == 1
        assert roster[0]["id"] == enrollment_a["id"]
        assert roster[0]["student"]["nim"] == nim
        assert roster[0]["student"]["full_name"] == "Budi Santoso"

        # Delete one enrollment -> 204
        r = await c.delete(
            f"/classes/{class_a['id']}/enrollments/{enrollment_a['id']}",
            headers=headers,
        )
        assert r.status_code == 204, r.text

        r = await c.get(f"/classes/{class_a['id']}/roster", headers=headers)
        assert r.status_code == 200, r.text
        assert r.json() == []

        # Deleting the same enrollment again -> 404
        r = await c.delete(
            f"/classes/{class_a['id']}/enrollments/{enrollment_a['id']}",
            headers=headers,
        )
        assert r.status_code == 404, r.text

        # A new student can be created from NIM alone (optional fields omitted)
        r = await c.post(
            f"/classes/{class_a['id']}/enrollments",
            headers=headers,
            json={"nim": nim2},
        )
        assert r.status_code == 201, r.text
        enrollment_c = r.json()
        assert enrollment_c["student"]["nim"] == nim2
        assert enrollment_c["student"]["full_name"] == nim2
        assert enrollment_c["student"]["email"] is None

        # Lecturers cannot change shared student records.
        r = await c.patch(
            f"/students/{enrollment_c['student']['id']}",
            headers=headers,
            json={"full_name": "Nama baru"},
        )
        assert r.status_code == 403, r.text
        r = await c.delete(
            f"/students/{enrollment_c['student']['id']}",
            headers=headers,
        )
        assert r.status_code == 403, r.text

        # An admin cannot delete a student who is still enrolled -> 409
        r = await c.delete(
            f"/students/{enrollment_c['student']['id']}",
            headers=admin_headers,
        )
        assert r.status_code == 409, r.text

        # Remove the enrollment so the student can be deleted through the API
        r = await c.delete(
            f"/classes/{class_a['id']}/enrollments/{enrollment_c['id']}",
            headers=headers,
        )
        assert r.status_code == 204, r.text
        r = await c.delete(
            f"/students/{enrollment_c['student']['id']}",
            headers=admin_headers,
        )
        assert r.status_code == 204, r.text

        # Class with an enrollment cannot be deleted -> 409
        r = await c.delete(f"/classes/{class_b['id']}", headers=headers)
        assert r.status_code == 409, r.text

        # Remove the remaining enrollment and delete the class
        r = await c.delete(
            f"/classes/{class_b['id']}/enrollments/{enrollment_b['id']}",
            headers=headers,
        )
        assert r.status_code == 204, r.text
        r = await c.delete(f"/classes/{class_b['id']}", headers=headers)
        assert r.status_code == 204, r.text
        r = await c.get(f"/classes/{class_b['id']}", headers=headers)
        assert r.status_code == 404

        # Update class section
        r = await c.patch(
            f"/classes/{class_a['id']}",
            headers=headers,
            json={"section": "C"},
        )
        assert r.status_code == 200, r.text
        assert r.json()["section"] == "C"

    await _cleanup(class_ids, course_ids, nims, [lecturer_email])


@pytest.mark.asyncio
async def test_class_lecturer_scoping_and_superadmin_override():
    suffix = uuid.uuid4().hex[:8]
    email1 = f"dosen-satu-{suffix}@example.com"
    email2 = f"dosen-dua-{suffix}@example.com"
    course_code = f"SCO{suffix}".upper()
    nim = f"SCN{suffix}".upper()
    class_ids: list[str] = []
    course_ids: list[str] = []
    nims = [nim]
    user_emails = [email1, email2]

    async with AsyncClient(app=app, base_url="http://test") as c:
        admin_token = await _login(c, "admin@example.com", "admin123")
        admin_headers = _headers(admin_token)
        lecturer1_id = await _create_lecturer(c, admin_headers, email1, "Dosen Satu")
        lecturer2_id = await _create_lecturer(c, admin_headers, email2, "Dosen Dua")
        course_id = await _create_course(c, admin_headers, course_code)
        course_ids.append(course_id)

        token1 = await _login(c, email1, "rahasia123")
        token2 = await _login(c, email2, "rahasia123")
        headers1 = _headers(token1)
        headers2 = _headers(token2)

        # Lecturer 1 cannot assign the class to another lecturer
        r = await c.post(
            "/classes",
            headers=headers1,
            json={
                "course_id": course_id,
                "section": "A",
                "academic_year": "2026/2027",
                "lecturer_id": lecturer2_id,
            },
        )
        assert r.status_code == 403, r.text

        # Lecturer 1 creates their own class
        r = await c.post(
            "/classes",
            headers=headers1,
            json={
                "course_id": course_id,
                "section": "A",
                "academic_year": "2026/2027",
            },
        )
        assert r.status_code == 201, r.text
        class1 = r.json()
        class_ids.append(class1["id"])
        assert class1["lecturer_id"] == lecturer1_id

        # Enroll a student in class 1
        r = await c.post(
            f"/classes/{class1['id']}/enrollments",
            headers=headers1,
            json={"nim": nim, "full_name": "Citra Dewi"},
        )
        assert r.status_code == 201, r.text
        enrollment_id = r.json()["id"]

        # Superadmin can create a class for a specific lecturer
        r = await c.post(
            "/classes",
            headers=admin_headers,
            json={
                "course_id": course_id,
                "section": "B",
                "academic_year": "2026/2027",
                "lecturer_id": lecturer2_id,
            },
        )
        assert r.status_code == 201, r.text
        class2 = r.json()
        class_ids.append(class2["id"])
        assert class2["lecturer_id"] == lecturer2_id

        # Superadmin must name a lecturer
        r = await c.post(
            "/classes",
            headers=admin_headers,
            json={
                "course_id": course_id,
                "section": "C",
                "academic_year": "2026/2027",
            },
        )
        assert r.status_code == 422, r.text

        # Superadmin sees all classes; each lecturer sees only their own
        r = await c.get("/classes", headers=admin_headers)
        assert r.status_code == 200, r.text
        admin_ids = [item["id"] for item in r.json()]
        assert class1["id"] in admin_ids
        assert class2["id"] in admin_ids

        r = await c.get("/classes", headers=headers1)
        assert r.status_code == 200, r.text
        lecturer1_ids = [item["id"] for item in r.json()]
        assert class1["id"] in lecturer1_ids
        assert class2["id"] not in lecturer1_ids

        r = await c.get("/classes", headers=headers2)
        assert r.status_code == 200, r.text
        lecturer2_ids = [item["id"] for item in r.json()]
        assert class2["id"] in lecturer2_ids
        assert class1["id"] not in lecturer2_ids

        # Lecturer 2 cannot read, update, delete, roster, or enroll into class 1
        r = await c.get(f"/classes/{class1['id']}", headers=headers2)
        assert r.status_code == 403, r.text
        r = await c.patch(
            f"/classes/{class1['id']}", headers=headers2, json={"section": "Z"}
        )
        assert r.status_code == 403, r.text
        r = await c.delete(f"/classes/{class1['id']}", headers=headers2)
        assert r.status_code == 403, r.text
        r = await c.get(f"/classes/{class1['id']}/roster", headers=headers2)
        assert r.status_code == 403, r.text
        r = await c.post(
            f"/classes/{class1['id']}/enrollments",
            headers=headers2,
            json={"nim": f"OTHER{suffix}".upper()},
        )
        assert r.status_code == 403, r.text
        r = await c.delete(
            f"/classes/{class1['id']}/enrollments/{enrollment_id}",
            headers=headers2,
        )
        assert r.status_code == 403, r.text

        # Class 1 is unchanged for its owner
        r = await c.get(f"/classes/{class1['id']}", headers=headers1)
        assert r.status_code == 200, r.text
        assert r.json()["section"] == "A"
        r = await c.get(f"/classes/{class1['id']}/roster", headers=headers1)
        assert r.status_code == 200, r.text
        assert len(r.json()) == 1

        # Superadmin can update any class and reassign its lecturer
        r = await c.patch(
            f"/classes/{class1['id']}",
            headers=admin_headers,
            json={"section": "A2", "lecturer_id": lecturer2_id},
        )
        assert r.status_code == 200, r.text
        assert r.json()["section"] == "A2"
        assert r.json()["lecturer_id"] == lecturer2_id

        # After reassignment, lecturer 2 can manage class 1
        r = await c.get(f"/classes/{class1['id']}", headers=headers2)
        assert r.status_code == 200, r.text
        r = await c.get(f"/classes/{class1['id']}/roster", headers=headers2)
        assert r.status_code == 200, r.text
        assert len(r.json()) == 1

        # Superadmin can delete a class once its enrollments are removed
        r = await c.delete(
            f"/classes/{class1['id']}/enrollments/{enrollment_id}",
            headers=admin_headers,
        )
        assert r.status_code == 204, r.text
        r = await c.delete(f"/classes/{class1['id']}", headers=admin_headers)
        assert r.status_code == 204, r.text

    await _cleanup(class_ids, course_ids, nims, user_emails)


@pytest.mark.asyncio
async def test_classes_require_authentication():
    async with AsyncClient(app=app, base_url="http://test") as c:
        r = await c.get("/classes")
        assert r.status_code == 401
