"""Uji relasi kelas/roster dan komentar database.

Tests for the Class, Student, and Enrollment models and their DB
comments.

Persistence relasi kelas/mahasiswa/enrollment serta komentar katalog
PostgreSQL.

Memerlukan PostgreSQL disposable yang sudah dimigrasi; beberapa skenario
melakukan commit nyata.
"""

import uuid

import pytest
from sqlalchemy import text

from app.database import AsyncSessionLocal
from app.models.class_ import Class
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.student import Student
from app.models.user import User, UserRole


async def _column_comments(session, table_name: str) -> list[tuple[str, str | None]]:
    """Baca komentar kolom dari katalog PostgreSQL."""
    result = await session.execute(
        text(
            """
            SELECT a.attname, pg_catalog.col_description(c.oid, a.attnum)
            FROM pg_catalog.pg_attribute a
            JOIN pg_catalog.pg_class c ON a.attrelid = c.oid
            JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
            WHERE n.nspname = 'public'
              AND c.relname = :table_name
              AND a.attnum > 0
              AND NOT a.attisdropped
            """
        ),
        {"table_name": table_name},
    )
    return result.all()


async def _table_comment(session, table_name: str) -> str | None:
    """Baca komentar tabel dari katalog PostgreSQL."""
    result = await session.execute(
        text(
            """
            SELECT pg_catalog.obj_description(c.oid, 'pg_class')
            FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
            WHERE n.nspname = 'public' AND c.relname = :table_name
            """
        ),
        {"table_name": table_name},
    )
    return result.scalar_one_or_none()


@pytest.mark.asyncio
async def test_class_student_enrollment_model_and_comments():
    """Periksa relasi dan komentar schema hasil migration."""
    suffix = uuid.uuid4().hex[:8]
    email = f"class-model-{suffix}@example.com"
    async with AsyncSessionLocal() as session:
        lecturer = User(
            email=email,
            password_hash="hash",
            full_name="Dosen Pemodelan",
            role=UserRole.LECTURER,
        )
        session.add(lecturer)
        await session.commit()
        await session.refresh(lecturer)

        course = Course(
            code=f"MODELK-{suffix}".upper(),
            name="Pemodelan Kelas",
            credits=3,
            semester="2026/1",
            created_by=lecturer.id,
        )
        session.add(course)
        await session.commit()
        await session.refresh(course)

        student = Student(
            nim=f"MODELNIM-{suffix}".upper(),
            full_name="Mahasiswa Pemodelan",
            email=f"mahasiswa-{suffix}@example.com",
        )
        session.add(student)
        await session.commit()
        await session.refresh(student)

        class_ = Class(
            course_id=course.id,
            section="A",
            lecturer_id=lecturer.id,
            academic_year="2026/2027",
        )
        session.add(class_)
        await session.commit()
        await session.refresh(class_)

        enrollment = Enrollment(class_id=class_.id, student_id=student.id)
        session.add(enrollment)
        await session.commit()
        await session.refresh(enrollment)

        assert student.id is not None
        assert student.nim.upper().startswith("MODELNIM-")
        assert student.full_name == "Mahasiswa Pemodelan"
        assert student.created_at is not None

        assert class_.id is not None
        assert class_.course_id == course.id
        assert class_.section == "A"
        assert class_.lecturer_id == lecturer.id
        assert class_.academic_year == "2026/2027"
        assert class_.created_at is not None

        assert enrollment.id is not None
        assert enrollment.class_id == class_.id
        assert enrollment.student_id == student.id
        assert enrollment.enrolled_at is not None

        expected_columns = {"students": 5, "classes": 6, "enrollments": 4}
        for table_name, column_count in expected_columns.items():
            rows = await _column_comments(session, table_name)
            assert len(rows) == column_count, table_name
            for col_name, comment in rows:
                assert comment, f"missing comment for {table_name}.{col_name}"
            assert await _table_comment(session, table_name), (
                f"missing table comment for {table_name}"
            )

        # Cleanup in FK order
        await session.delete(enrollment)
        await session.commit()
        await session.delete(class_)
        await session.commit()
        await session.delete(student)
        await session.commit()
        await session.delete(course)
        await session.commit()
        await session.delete(lecturer)
        await session.commit()
