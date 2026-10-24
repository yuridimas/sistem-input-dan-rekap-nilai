import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.main import app
from app.models.user import User, UserRole
from app.services.auth import hash_password


@pytest.mark.asyncio
async def test_login_success():
    async with AsyncClient(app=app, base_url="http://test") as c:
        r = await c.post("/auth/login", json={"email": "admin@example.com", "password": "admin123"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_bad_creds():
    async with AsyncClient(app=app, base_url="http://test") as c:
        r = await c.post("/auth/login", json={"email": "admin@example.com", "password": "wrong"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_login_missing():
    async with AsyncClient(app=app, base_url="http://test") as c:
        r = await c.post("/auth/login", json={})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_me_and_refresh():
    async with AsyncClient(app=app, base_url="http://test") as c:
        r = await c.post("/auth/login", json={"email": "admin@example.com", "password": "admin123"})
        tokens = r.json()
        r2 = await c.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
        assert r2.status_code == 200
        assert r2.json()["email"] == "admin@example.com"

        r3 = await c.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
        assert r3.status_code == 200
        new_tokens = r3.json()
        assert new_tokens["access_token"] != tokens["access_token"]


@pytest.mark.asyncio
async def test_role_guard_forbidden():
    email = f"lect-{uuid.uuid4()}@example.com"
    async with AsyncSessionLocal() as session:
        user = User(
            email=email,
            password_hash=hash_password("secret123"),
            full_name="Lecturer",
            role=UserRole.LECTURER,
            is_active=True,
        )
        session.add(user)
        await session.commit()

    async with AsyncClient(app=app, base_url="http://test") as c:
        r = await c.post("/auth/login", json={"email": email, "password": "secret123"})
        token = r.json()["access_token"]
        # superadmin-only endpoint
        r2 = await c.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r2.status_code == 200

    from app.dependencies import require_role
    from fastapi import Depends

    # register a temporary superadmin-only endpoint on the app
    @app.get("/_test_admin_only")
    async def _admin_only(user=Depends(require_role("superadmin"))):
        return {"ok": True}

    async with AsyncClient(app=app, base_url="http://test") as c:
        r = await c.get("/_test_admin_only", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403, r.text

        # superadmin token -> 200
        r_login = await c.post("/auth/login", json={"email": "admin@example.com", "password": "admin123"})
        admin_token = r_login.json()["access_token"]
        r3 = await c.get("/_test_admin_only", headers={"Authorization": f"Bearer {admin_token}"})
        assert r3.status_code == 200, r3.text

    # cleanup user
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        u = result.scalar_one()
        await session.delete(u)
        await session.commit()