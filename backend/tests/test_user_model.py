"""Persistence akun dan metadata komentar PostgreSQL.

Memerlukan PostgreSQL disposable yang dimigrasi; beberapa skenario
melakukan commit nyata.
"""
import uuid

import pytest
from sqlalchemy import text

from app.database import AsyncSessionLocal
from app.models.user import User, UserRole


@pytest.mark.asyncio
async def test_user_model_insert_and_comments():
    """Periksa default akun dan komentar kolom pada DB."""
    email = f"test-{uuid.uuid4()}@example.com"
    async with AsyncSessionLocal() as session:
        user = User(
            email=email,
            password_hash="hash",
            full_name="Test User",
            role=UserRole.LECTURER,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        assert user.id is not None
        assert user.email == email
        assert user.full_name == "Test User"
        assert user.role == "lecturer"
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is not None

        # Verify Bahasa Indonesia comments exist for every column.
        result = await session.execute(
            text(
                """
                SELECT a.attname, pg_catalog.col_description(c.oid, a.attnum)
                FROM pg_catalog.pg_attribute a
                JOIN pg_catalog.pg_class c ON a.attrelid = c.oid
                JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
                WHERE n.nspname = 'public'
                  AND c.relname = 'users'
                  AND a.attnum > 0
                  AND NOT a.attisdropped
                """
            )
        )
        rows = result.all()
        assert len(rows) == 8
        for col_name, comment in rows:
            assert comment, f"missing comment for column {col_name}"

        # Cleanup
        await session.delete(user)
        await session.commit()