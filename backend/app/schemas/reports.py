"""Report data shared by PDF rendering and later spreadsheet exports."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ReportRow(BaseModel):
    enrollment_id: uuid.UUID
    nim: str
    full_name: str
    final_score: Decimal
    rank: int | None
    finalized_at: datetime | None


class ReportComponent(BaseModel):
    id: uuid.UUID
    name: str
    category: str
    weight: Decimal
    max_score: Decimal
    score: Decimal | None


class ReportData(BaseModel):
    class_id: uuid.UUID
    course_name: str
    course_code: str
    semester: str
    section: str
    academic_year: str
    rows: list[ReportRow]
    components: list[ReportComponent] = Field(default_factory=list)
    component_scores: dict[uuid.UUID, dict[uuid.UUID, Decimal | None]] = Field(default_factory=dict)
