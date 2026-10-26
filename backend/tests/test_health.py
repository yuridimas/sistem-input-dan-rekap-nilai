"""Kontrak health ketika dependensi tidak siap.

ASGI memanggil probe DB/Redis yang hanya membaca; tidak menyiapkan data.
"""
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_health_ok():
    """Pertahankan status HTTP ok terpisah dari flag readiness."""
    async with AsyncClient(app=app, base_url="http://test") as c:
        r = await c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"