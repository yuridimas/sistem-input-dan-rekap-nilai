"""Course model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class Course(Base):
    __tablename__ = "courses"
    __table_args__ = {"comment": "Tabel mata kuliah"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Identitas unik mata kuliah",
    )
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="Kode mata kuliah (unik)",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Nama mata kuliah",
    )
    credits: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Jumlah SKS",
    )
    semester: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Semester (mis. 2026/1)",
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="Pengguna yang membuat data mata kuliah",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Waktu pembuatan data mata kuliah",
    )
