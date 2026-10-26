"""Tests for student CRUD and duplicate NIM handling.

Profil global, NIM unik, dan autentikasi.

Memerlukan PostgreSQL disposable yang dimigrasi; beberapa skenario
melakukan commit nyata.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import delete

from app.database import AsyncSessionLocal
from app.main import app
from app.models.student import Student


async def _login(client: AsyncClient, email: str, password: str) -> str:
    """Login melalui API untuk mendapat token skenario."""
    r = await client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    """Bentuk header bearer dari token skenario."""
    return {"Authorization": f"Bearer {token}"}


async def _cleanup(nims: list[str]) -> None:
    """Hapus data skenario sesuai urutan relasi."""
    if not nims:
        return
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Student).where(Student.nim.in_(nims)))
        await session.commit()


@pytest.mark.asyncio
async def test_student_crud_and_duplicate_nim():
    """NIM duplikat ditolak dan perubahan profil dapat dibaca kembali.
    """
    suffix = uuid.uuid4().hex[:8]
    nim = f"NIM{suffix}".upper()
    other_nim = f"NIMX{suffix}".upper()
    nims = [nim, other_nim]

    async with AsyncClient(app=app, base_url="http://test") as c:
        token = await _login(c, "admin@example.com", "admin123")
        headers = _headers(token)

        # Create
        payload = {
            "nim": nim,
            "full_name": "Budi Santoso",
            "email": f"budi-{suffix}@example.com",
        }
        r = await c.post("/students", headers=headers, json=payload)
        assert r.status_code == 201, r.text
        created = r.json()
        assert created["nim"] == nim
        assert created["full_name"] == "Budi Santoso"
        assert created["email"] == payload["email"]
        assert created["created_at"]

        # Duplicate NIM -> 409
        r = await c.post(
            "/students",
            headers=headers,
            json={**payload, "full_name": "Duplikat"},
        )
        assert r.status_code == 409, r.text

        # List contains the new student
        r = await c.get("/students", headers=headers)
        assert r.status_code == 200, r.text
        assert created["id"] in [student["id"] for student in r.json()]

        # Get
        r = await c.get(f"/students/{created['id']}", headers=headers)
        assert r.status_code == 200, r.text
        assert r.json()["nim"] == nim

        # Second student, used to verify duplicate NIM on update
        r = await c.post(
            "/students",
            headers=headers,
            json={"nim": other_nim, "full_name": "Siti Aminah"},
        )
        assert r.status_code == 201, r.text
        other_id = r.json()["id"]

        # Update
        r = await c.patch(
            f"/students/{created['id']}",
            headers=headers,
            json={"full_name": "Budi Santoso Jaya"},
        )
        assert r.status_code == 200, r.text
        assert r.json()["full_name"] == "Budi Santoso Jaya"
        assert r.json()["nim"] == nim

        # Updating to an existing NIM -> 409
        r = await c.patch(
            f"/students/{created['id']}",
            headers=headers,
            json={"nim": other_nim},
        )
        assert r.status_code == 409, r.text

        # Delete
        r = await c.delete(f"/students/{created['id']}", headers=headers)
        assert r.status_code == 204, r.text
        r = await c.get(f"/students/{created['id']}", headers=headers)
        assert r.status_code == 404

        # Cleanup the second student through the API
        r = await c.delete(f"/students/{other_id}", headers=headers)
        assert r.status_code == 204, r.text

    await _cleanup(nims)


@pytest.mark.asyncio
async def test_students_require_authentication():
    """Endpoint profil harus menolak akses anonim."""
    async with AsyncClient(app=app, base_url="http://test") as c:
        r = await c.get("/students")
        assert r.status_code == 401
