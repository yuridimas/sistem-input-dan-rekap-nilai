"""Draft grade and class grade grid responses."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.grade import GradeStatus
from app.schemas.component import ComponentRead
from app.schemas.student import StudentRead


class GradeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    enrollment_id: uuid.UUID
    final_score: Decimal
    status: GradeStatus
    finalized_at: datetime | None
    finalized_by: uuid.UUID | None
    release_notified_at: datetime | None


class GradeRowRead(BaseModel):
    enrollment_id: uuid.UUID
    student: StudentRead
    scores: dict[uuid.UUID, Decimal]
    final_score: Decimal | None
    status: GradeStatus


class ClassGradesRead(BaseModel):
    class_id: uuid.UUID
    components: list[ComponentRead]
    grades: list[GradeRowRead]
