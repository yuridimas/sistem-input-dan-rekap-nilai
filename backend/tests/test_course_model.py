"""Tests for the Course model and its database comments."""

import uuid

import pytest
from sqlalchemy import text

from app.database import AsyncSessionLocal
from app.models.course import Course
from app.models.user import User, UserRole


@pytest.mark.asyncio
async def test_course_model_insert_and_comments():
    email = f"course-model-{uuid.uuid4()}@example.com"
    async with AsyncSessionLocal() as session:
        creator = User(
            email=email,
            password_hash="hash",
            full_name="Pembuat Mata Kuliah",
            role=UserRole.LECTURER,
        )
        session.add(creator)
        await session.commit()
        await session.refresh(creator)

        course = Course(
            code=f"MODEL-{uuid.uuid4().hex[:8]}".upper(),
            name="Pemodelan Data",
            credits=3,
            semester="2026/1",
            created_by=creator.id,
        )
        session.add(course)
        await session.commit()
        await session.refresh(course)

        assert course.id is not None
        assert course.code.startswith("MODEL-")
        assert course.name == "Pemodelan Data"
        assert course.credits == 3
        assert course.semester == "2026/1"
        assert course.created_by == creator.id
        assert course.created_at is not None

        # Verify Bahasa Indonesia comments exist for every column.
        result = await session.execute(
            text(
                """
                SELECT a.attname, pg_catalog.col_description(c.oid, a.attnum)
                FROM pg_catalog.pg_attribute a
                JOIN pg_catalog.pg_class c ON a.attrelid = c.oid
                JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
                WHERE n.nspname = 'public'
                  AND c.relname = 'courses'
                  AND a.attnum > 0
                  AND NOT a.attisdropped
                """
            )
        )
        rows = result.all()
        assert len(rows) == 7
        for col_name, comment in rows:
            assert comment, f"missing comment for column {col_name}"

        # Verify the table itself has a comment.
        result = await session.execute(
            text(
                """
                SELECT pg_catalog.obj_description(c.oid, 'pg_class')
                FROM pg_catalog.pg_class c
                JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
                WHERE n.nspname = 'public' AND c.relname = 'courses'
                """
            )
        )
        assert result.scalar_one()

        # Cleanup (course before user because of the created_by foreign key)
        await session.delete(course)
        await session.commit()
        await session.delete(creator)
        await session.commit()
