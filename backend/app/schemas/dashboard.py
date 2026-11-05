"""Read-only academic dashboard summaries.

Kontrak ringkasan baca untuk router dashboard dan halaman dashboard
frontend.

Batas field pada schema menjaga input; aturan relasi dan otorisasi tetap
berada di service.
"""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class DashboardClassRead(BaseModel):
    """Status rilis kelas berdasarkan kelengkapan finalisasi."""

    id: uuid.UUID
    section: str
    academic_year: str
    student_count: int
    status: Literal["pending", "released"]
    released_at: datetime | None


class DashboardCourseRead(BaseModel):
    """Mata kuliah dengan kelompok kelas yang terlihat."""

    id: uuid.UUID
    code: str
    name: str
    semester: str
    created_at: datetime
    classes: list[DashboardClassRead]


class DashboardReleaseRead(DashboardClassRead):
    """Konteks mata kuliah tambahan untuk daftar rilis lintas kelas."""

    course_id: uuid.UUID
    course_code: str
    course_name: str


class DashboardSummaryRead(BaseModel):
    """Hitungan dan kelompok data siap tampil pada dashboard."""

    course_count: int
    class_count: int
    pending_class_count: int
    courses: list[DashboardCourseRead]
    recently_released: list[DashboardReleaseRead]
