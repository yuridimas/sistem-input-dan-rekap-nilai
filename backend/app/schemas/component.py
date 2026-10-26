"""Component request and response contracts.

Kontrak komponen bagi router, validasi konfigurasi, dan perhitungan
nilai.

Batas field pada schema menjaga input; aturan relasi dan otorisasi tetap
berada di service.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.component import ComponentCategory

# Decimal membatasi presisi input; 2147483647 pada urutan mengikuti batas Integer PostgreSQL.
Weight = Annotated[Decimal, Field(gt=0, le=100, max_digits=5, decimal_places=2)]
MaxScore = Annotated[Decimal, Field(gt=0, max_digits=6, decimal_places=2)]


class ComponentCreate(BaseModel):
    """Masukan satu komponen; aturan lintas komponen di service."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    category: ComponentCategory
    weight: Weight
    max_score: MaxScore = Decimal("100")
    order_index: int = Field(default=0, ge=0, le=2147483647)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        """Terapkan normalisasi teks bersama tanpa menulis ke database.

        Args:
            value: Nilai field yang dinormalisasi atau divalidasi.

        Returns:
            Teks hasil trim yang tidak kosong.

        Raises:
            ValueError: bila teks wajib kosong.
        """
        value = value.strip()
        if not value:
            raise ValueError("Nama komponen tidak boleh kosong")
        return value


class ComponentUpdate(BaseModel):
    """Patch komponen dengan penolakan null eksplisit."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=100)
    category: ComponentCategory | None = None
    weight: Weight | None = None
    max_score: MaxScore | None = None
    order_index: int | None = Field(default=None, ge=0, le=2147483647)

    @field_validator("*")
    @classmethod
    def reject_null(cls, value: Any) -> Any:
        """Bedakan field absen dari null eksplisit pada patch.

        Field yang tidak dikirim memakai default tanpa melewati
        validator ini.

        Args:
            value: Nilai field yang dinormalisasi atau divalidasi.

        Returns:
            Nilai field semula jika bukan None.

        Raises:
            ValueError: untuk None yang dikirim.
        """
        if value is None:
            raise ValueError("Nilai tidak boleh null")
        return value

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        """Terapkan normalisasi teks bersama tanpa menulis ke database.

        Args:
            value: Nilai field yang dinormalisasi atau divalidasi.

        Returns:
            Teks hasil trim yang tidak kosong.

        Raises:
            ValueError: bila teks wajib kosong.
        """
        return ComponentCreate.strip_name(value)


class ComponentWrite(ComponentCreate):
    """Konfigurasi lengkap dengan ID opsional untuk komponen baru.

    Complete configuration row; retain an existing id or omit it to add
    one.
    """

    id: uuid.UUID | None = None


class ComponentRead(ComponentCreate):
    """Konfigurasi komponen dengan identitas database."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    class_id: uuid.UUID
    created_at: datetime
