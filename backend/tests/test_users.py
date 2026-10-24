"""Tests for superadmin user management (lecturer CRUD)."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.main import app
from app.models.user import User


async def _admin_token(client: AsyncClient) -> str:
    r = await client.post("/auth/login", json={"email": "admin@example.com", "password": "admin123"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.mark.asyncio
async def test_create_list_get_update_deactivate_lecturer():
    email = f"dosen-{uuid.uuid4()}@example.com"
    new_email = f"dosen-baru-{uuid.uuid4()}@example.com"
    created_id: str | None = None
    async with AsyncClient(app=app, base_url="http://test") as c:
        token = await _admin_token(c)
        headers = {"Authorization": f"Bearer {token}"}

        # Create
        r = await c.post(
            "/admin/users",
            headers=headers,
            json={
                "email": email,
                "password": "rahasia123",
                "full_name": "Dosen Baru",
                "role": "lecturer",
            },
        )
        assert r.status_code == 201, r.text
        created = r.json()
        created_id = created["id"]
        assert created["email"] == email
        assert created["role"] == "lecturer"
        assert created["is_active"] is True
        assert "password" not in created

        # List
        r = await c.get("/admin/users", headers=headers)
        assert r.status_code == 200, r.text
        ids = [u["id"] for u in r.json()]
        assert created_id in ids

        # Get
        r = await c.get(f"/admin/users/{created_id}", headers=headers)
        assert r.status_code == 200
        assert r.json()["email"] == email

        # Update
        r = await c.patch(
            f"/admin/users/{created_id}",
            headers=headers,
            json={"full_name": "Dosen Diperbarui", "email": new_email},
        )
        assert r.status_code == 200, r.text
        assert r.json()["full_name"] == "Dosen Diperbarui"
        assert r.json()["email"] == new_email

        # Deactivate (DELETE)
        r = await c.delete(f"/admin/users/{created_id}", headers=headers)
        assert r.status_code == 204, r.text

        r = await c.get(f"/admin/users/{created_id}", headers=headers)
        assert r.status_code == 200
        assert r.json()["is_active"] is False

        # Deactivated user cannot log in
        r = await c.post("/auth/login", json={"email": new_email, "password": "rahasia123"})
        assert r.status_code == 401

    # Cleanup
    if created_id:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.id == uuid.UUID(created_id)))
            user = result.scalar_one_or_none()
            if user is not None:
                await session.delete(user)
                await session.commit()


@pytest.mark.asyncio
async def test_duplicate_email_conflict():
    email = f"dupe-{uuid.uuid4()}@example.com"
    created_ids: list[str] = []
    async with AsyncClient(app=app, base_url="http://test") as c:
        token = await _admin_token(c)
        headers = {"Authorization": f"Bearer {token}"}
        body = {"email": email, "password": "rahasia123", "full_name": "Duplikat"}
        r1 = await c.post("/admin/users", headers=headers, json=body)
        assert r1.status_code == 201, r1.text
        created_ids.append(r1.json()["id"])

        r2 = await c.post("/admin/users", headers=headers, json=body)
        assert r2.status_code == 409, r2.text

    async with AsyncSessionLocal() as session:
        for cid in created_ids:
            result = await session.execute(select(User).where(User.id == uuid.UUID(cid)))
            user = result.scalar_one_or_none()
            if user is not None:
                await session.delete(user)
        await session.commit()


@pytest.mark.asyncio
async def test_lecturer_forbidden():
    email = f"onlydosen-{uuid.uuid4()}@example.com"
    created_id: str | None = None
    async with AsyncClient(app=app, base_url="http://test") as c:
        token = await _admin_token(c)
        headers = {"Authorization": f"Bearer {token}"}
        r = await c.post(
            "/admin/users",
            headers=headers,
            json={"email": email, "password": "rahasia123", "full_name": "Dosen"},
        )
        assert r.status_code == 201, r.text
        created_id = r.json()["id"]

        r = await c.post("/auth/login", json={"email": email, "password": "rahasia123"})
        lecturer_token = r.json()["access_token"]

        r = await c.get("/admin/users", headers={"Authorization": f"Bearer {lecturer_token}"})
        assert r.status_code == 403

    async with AsyncSessionLocal() as session:
        if created_id:
            result = await session.execute(select(User).where(User.id == uuid.UUID(created_id)))
            user = result.scalar_one_or_none()
            if user is not None:
                await session.delete(user)
                await session.commit()
