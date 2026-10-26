"""Class, enrollment, and roster request/response schemas.

Kontrak kelas dan roster bagi router classes dan service pengelolaan.

Batas field pada schema menjaga input; aturan relasi dan otorisasi tetap
berada di service.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.student import StudentRead, _validate_email


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


class ClassCreate(BaseModel):
    """Masukan kelas dengan penugasan dosen sesuai role pembuat."""

    course_id: uuid.UUID
    section: str = Field(..., min_length=1, max_length=10)
    academic_year: str = Field(..., min_length=1, max_length=20)
    lecturer_id: Optional[uuid.UUID] = None

    @field_validator("section", "academic_year")
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


class ClassUpdate(BaseModel):
    """Patch kelas; None berarti mempertahankan metadata lama."""

    section: Optional[str] = Field(None, min_length=1, max_length=10)
    academic_year: Optional[str] = Field(None, min_length=1, max_length=20)
    lecturer_id: Optional[uuid.UUID] = None

    @field_validator("section", "academic_year")
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


class ClassRead(BaseModel):
    """Metadata kelas beserta penanda penguncian finalisasi."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    section: str
    lecturer_id: uuid.UUID
    academic_year: str
    created_at: datetime
    has_finalized_grades: bool = False


class EnrollmentCreate(BaseModel):
    """Masukan NIM untuk memakai ulang atau membuat profil.

    Service membuat profil hanya ketika NIM belum terdaftar.
    """

    nim: str = Field(..., min_length=1, max_length=50)
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


class RosterEntryRead(BaseModel):
    """Keikutsertaan kelas beserta profil mahasiswa."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    enrolled_at: datetime
    student: StudentRead
