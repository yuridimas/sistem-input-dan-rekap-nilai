"""Component request and response contracts."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.component import ComponentCategory

Weight = Annotated[Decimal, Field(gt=0, le=100, max_digits=5, decimal_places=2)]
MaxScore = Annotated[Decimal, Field(gt=0, max_digits=6, decimal_places=2)]


class ComponentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    category: ComponentCategory
    weight: Weight
    max_score: MaxScore = Decimal("100")
    order_index: int = Field(default=0, ge=0, le=2147483647)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Nama komponen tidak boleh kosong")
        return value


class ComponentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=100)
    category: ComponentCategory | None = None
    weight: Weight | None = None
    max_score: MaxScore | None = None
    order_index: int | None = Field(default=None, ge=0, le=2147483647)

    @field_validator("*")
    @classmethod
    def reject_null(cls, value: Any) -> Any:
        if value is None:
            raise ValueError("Nilai tidak boleh null")
        return value

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return ComponentCreate.strip_name(value)


class ComponentWrite(ComponentCreate):
    """Complete configuration row; retain an existing id or omit it to add one."""

    id: uuid.UUID | None = None


class ComponentRead(ComponentCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    class_id: uuid.UUID
    created_at: datetime
