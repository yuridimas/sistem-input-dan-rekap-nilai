"""Read-only academic dashboard summaries."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class DashboardClassRead(BaseModel):
    id: uuid.UUID
    section: str
    academic_year: str
    student_count: int
    status: Literal["pending", "released"]
    released_at: datetime | None


class DashboardCourseRead(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    semester: str
    classes: list[DashboardClassRead]


class DashboardReleaseRead(DashboardClassRead):
    course_id: uuid.UUID
    course_code: str
    course_name: str


class DashboardSummaryRead(BaseModel):
    course_count: int
    class_count: int
    pending_class_count: int
    courses: list[DashboardCourseRead]
    recently_released: list[DashboardReleaseRead]
