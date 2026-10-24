"""Course request/response schemas."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _validate_text(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Tidak boleh kosong")
    return value


class CourseCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    credits: int = Field(..., ge=1)
    semester: str = Field(..., min_length=1, max_length=20)

    @field_validator("code", "name", "semester")
    @classmethod
    def _strip(cls, value: str) -> str:
        return _validate_text(value)


class CourseUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    credits: Optional[int] = Field(None, ge=1)
    semester: Optional[str] = Field(None, min_length=1, max_length=20)

    @field_validator("code", "name", "semester")
    @classmethod
    def _strip(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return _validate_text(value)


class CourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    credits: int
    semester: str
    created_by: uuid.UUID
    created_at: datetime
