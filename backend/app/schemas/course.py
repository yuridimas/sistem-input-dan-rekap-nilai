"""Course request/response schemas.

Validasi masukan dan serialisasi mata kuliah untuk router/service
courses.

Batas field pada schema menjaga input; aturan relasi dan otorisasi tetap
berada di service.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _validate_text(value: str) -> str:
    """Tolak identitas atau nama yang kosong setelah trim.

    Tidak menulis state eksternal.

    Args:
        value: Nilai field yang dinormalisasi atau divalidasi.

    Raises:
        ValueError: jika hasil trim kosong.

    Returns:
        Teks hasil trim yang tidak kosong.
    """
    value = value.strip()
    if not value:
        raise ValueError("Tidak boleh kosong")
    return value


class CourseCreate(BaseModel):
    """Masukan mata kuliah dengan SKS positif."""

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    credits: int = Field(..., ge=1)
    semester: str = Field(..., min_length=1, max_length=20)

    @field_validator("code", "name", "semester")
    @classmethod
    def _strip(cls, value: str) -> str:
        """Terapkan normalisasi teks bersama tanpa menulis ke database.

        Args:
            value: Nilai field yang dinormalisasi atau divalidasi.

        Returns:
            Teks hasil trim yang tidak kosong.

        Raises:
            ValueError: bila teks wajib kosong.
        """
        return _validate_text(value)


class CourseUpdate(BaseModel):
    """Patch mata kuliah; None mempertahankan nilai lama."""

    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    credits: Optional[int] = Field(None, ge=1)
    semester: Optional[str] = Field(None, min_length=1, max_length=20)

    @field_validator("code", "name", "semester")
    @classmethod
    def _strip(cls, value: Optional[str]) -> Optional[str]:
        """Terapkan normalisasi teks bersama tanpa menulis ke database.

        Args:
            value: Nilai field yang dinormalisasi atau divalidasi.

        Returns:
            Teks hasil trim, atau None jika nilai opsional tidak diisi.

        Raises:
            ValueError: bila teks wajib kosong.
        """
        if value is None:
            return None
        return _validate_text(value)


class CourseRead(BaseModel):
    """Respons metadata mata kuliah yang dapat dibentuk dari objek ORM.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    credits: int
    semester: str
    created_by: uuid.UUID
    created_at: datetime
