"""Student request/response schemas.

Validasi profil mahasiswa yang dipakai router students dan schema
roster.

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


class StudentCreate(BaseModel):
    """Input identitas NIM/nama dengan email opsional untuk notifikasi.
    """

    nim: str = Field(..., min_length=1, max_length=50)
    full_name: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = Field(None, min_length=3, max_length=255)

    @field_validator("nim", "full_name")
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


class StudentUpdate(BaseModel):
    """Patch profil; email null eksplisit menghapus alamat lama."""

    nim: Optional[str] = Field(None, min_length=1, max_length=50)
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(None, min_length=3, max_length=255)

    @field_validator("nim", "full_name")
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


class StudentRead(BaseModel):
    """Profil mahasiswa tanpa identitas akun login."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nim: str
    full_name: str
    email: Optional[str] = None
    created_at: datetime
