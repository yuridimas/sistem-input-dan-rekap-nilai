"""Student request/response schemas."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _validate_text(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Tidak boleh kosong")
    return value


def _validate_email(value: str) -> str:
    value = value.strip().lower()
    if "@" not in value or "." not in value.split("@")[-1]:
        raise ValueError("Format email tidak valid")
    return value


class StudentCreate(BaseModel):
    nim: str = Field(..., min_length=1, max_length=50)
    full_name: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = Field(None, min_length=3, max_length=255)

    @field_validator("nim", "full_name")
    @classmethod
    def _strip(cls, value: str) -> str:
        return _validate_text(value)

    @field_validator("email")
    @classmethod
    def _email(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return _validate_email(value)


class StudentUpdate(BaseModel):
    nim: Optional[str] = Field(None, min_length=1, max_length=50)
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


class StudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nim: str
    full_name: str
    email: Optional[str] = None
    created_at: datetime
