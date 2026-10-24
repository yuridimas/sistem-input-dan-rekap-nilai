import asyncio

from fastapi import APIRouter
from sqlalchemy import text

from app.config import get_settings
from app.database import AsyncSessionLocal

router = APIRouter()


async def _ping_db() -> bool:
    try:
        async with AsyncSessionLocal() as session:
            await asyncio.wait_for(session.execute(text("SELECT 1")), timeout=2.0)
        return True
    except Exception:
        return False


async def _ping_redis() -> bool:
    try:
        import redis.asyncio as redis_async

        settings = get_settings()
        client = redis_async.from_url(settings.redis_url)
        try:
            await asyncio.wait_for(client.ping(), timeout=2.0)
            return True
        finally:
            await client.aclose()
    except Exception:
        return False


@router.get("/health")
async def health() -> dict:
    db_ok = await _ping_db()
    redis_ok = await _ping_redis()
    return {"status": "ok", "db": db_ok, "redis": redis_ok}