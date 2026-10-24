"""Class, enrollment, and roster request/response schemas."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.student import StudentRead, _validate_email


def _validate_text(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Tidak boleh kosong")
    return value


class ClassCreate(BaseModel):
    course_id: uuid.UUID
    section: str = Field(..., min_length=1, max_length=10)
    academic_year: str = Field(..., min_length=1, max_length=20)
    lecturer_id: Optional[uuid.UUID] = None

    @field_validator("section", "academic_year")
    @classmethod
    def _strip(cls, value: str) -> str:
        return _validate_text(value)


class ClassUpdate(BaseModel):
    section: Optional[str] = Field(None, min_length=1, max_length=10)
    academic_year: Optional[str] = Field(None, min_length=1, max_length=20)
    lecturer_id: Optional[uuid.UUID] = None

    @field_validator("section", "academic_year")
    @classmethod
    def _strip(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return _validate_text(value)


class ClassRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    section: str
    lecturer_id: uuid.UUID
    academic_year: str
    created_at: datetime


class EnrollmentCreate(BaseModel):
    nim: str = Field(..., min_length=1, max_length=50)
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(None, min_length=3, max_length=255)

    @field_validator("nim", "full_name")
    @classmethod
    def _strip(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return _validate_text(value)

    @field_validator("email")
    @classmethod
    def _email(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return _validate_email(value)


class RosterEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    enrolled_at: datetime
    student: StudentRead
