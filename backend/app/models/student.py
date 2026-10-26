"""Student model.

Data mahasiswa untuk roster, laporan, dan tujuan notifikasi; terpisah
dari akun.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class Student(Base):
    """Profil NIM global tanpa akun login mahasiswa."""

    __tablename__ = "students"
    __table_args__ = {
        "comment": "Tabel data mahasiswa (tanpa akun login)",
    }

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Identitas unik mahasiswa",
    )
    nim: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="Nomor Induk Mahasiswa (unik)",
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Nama lengkap mahasiswa",
    )
    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Email mahasiswa (untuk notifikasi rilis nilai)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Waktu pembuatan data mahasiswa",
    )
