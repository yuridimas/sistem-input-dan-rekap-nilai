"""User model."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class UserRole(str, Enum):
    """Peran pengguna dalam sistem."""

    SUPERADMIN = "superadmin"
    LECTURER = "lecturer"


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"comment": "Tabel pengguna sistem (superadmin dan dosen)"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Identitas unik pengguna",
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        comment="Alamat email pengguna (untuk login)",
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Hash kata sandi (bcrypt)",
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Nama lengkap pengguna",
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Peran: superadmin atau dosen",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        comment="Status aktif pengguna",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Waktu pembuatan akun",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Waktu pembaruan terakhir",
    )