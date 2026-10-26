"""User request/response schemas.

Kontrak pengelolaan akun untuk router users dan service password.

Batas field pada schema menjaga input; aturan relasi dan otorisasi tetap
berada di service.
"""

import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

Role = Literal["superadmin", "lecturer"]


def _validate_email(value: str) -> str:
    """Normalkan email dan periksa format dasarnya.

    Pemeriksaan format tidak memverifikasi keberadaan mailbox.

    Args:
        value: Nilai field yang dinormalisasi atau divalidasi.

    Returns:
        Email hasil trim/lowercase yang lolos format dasar.

    Raises:
        ValueError: untuk format dasar yang salah.
    """
    value = value.strip().lower()
    if "@" not in value or "." not in value.split("@")[-1]:
        raise ValueError("Format email tidak valid")
    return value


class UserCreate(BaseModel):
    """Masukan akun baru dengan hashing password di service."""

    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)
    role: Role = "lecturer"

    @field_validator("email")
    @classmethod
    def _email(cls, value: str) -> str:
        """Normalkan email akun baru dan periksa formatnya.

        Pemeriksaan format tidak memverifikasi keberadaan mailbox.

        Args:
            value: Nilai field yang dinormalisasi atau divalidasi.

        Returns:
            Email hasil trim/lowercase yang lolos format dasar.

        Raises:
            ValueError: untuk format dasar yang salah.
        """
        return _validate_email(value)


class UserUpdate(BaseModel):
    """Input parsial akun, termasuk reset password dan penonaktifan."""

    email: Optional[str] = Field(None, min_length=3, max_length=255)
    password: Optional[str] = Field(None, min_length=6, max_length=128)
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[Role] = None
    is_active: Optional[bool] = None

    @field_validator("email")
    @classmethod
    def _email(cls, value: Optional[str]) -> Optional[str]:
        """Normalkan email jika nilai opsionalnya diisi.

        Pemeriksaan format tidak memverifikasi keberadaan mailbox.

        Args:
            value: Nilai field yang dinormalisasi atau divalidasi.

        Returns:
            Email hasil trim/lowercase, atau None jika tidak diisi.

        Raises:
            ValueError: untuk format dasar yang salah.
        """
        if value is None:
            return None
        return _validate_email(value)


class UserRead(BaseModel):
    """Respons administratif tanpa password_hash."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
