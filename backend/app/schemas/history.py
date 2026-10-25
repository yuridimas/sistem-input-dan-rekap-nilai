"""Read-only views of released grades and their locked component data."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.component import ComponentCategory


class HistoryCourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    credits: int
    semester: str


class HistoryClassRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    section: str
    academic_year: str


class HistoryComponentRead(BaseModel):
    id: uuid.UUID
    name: str
    category: ComponentCategory
    weight: Decimal
    max_score: Decimal
    order_index: int
    score: Decimal | None


class HistoryRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    grade_id: uuid.UUID
    enrollment_id: uuid.UUID
    course: HistoryCourseRead
    class_: HistoryClassRead = Field(alias="class")
    final_score: Decimal
    rank: int | None
    finalized_at: datetime | None
    components: list[HistoryComponentRead]
