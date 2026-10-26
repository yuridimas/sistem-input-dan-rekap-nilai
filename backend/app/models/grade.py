"""Computed grades and their release state.

Hasil kalkulasi yang dikelola service scores/finalisasi dan dibaca
laporan.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class GradeStatus(StrEnum):
    """Status draft atau final untuk penguncian hasil penilaian."""

    DRAFT = "draft"
    FINALIZED = "finalized"


class Grade(Base):
    """Total satu enrollment beserta jejak rilis dan notifikasi."""

    __tablename__ = "grades"
    __table_args__ = (
        CheckConstraint("status IN ('draft', 'finalized')", name="ck_grades_status"),
        CheckConstraint("final_score >= 0 AND final_score <= 100", name="ck_grades_final_score"),
        {"comment": "Tabel nilai akhir dan status rilis mahasiswa"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="Identitas unik nilai akhir",
    )
    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("enrollments.id"), nullable=False, unique=True, index=True,
        comment="Pendaftaran mahasiswa pemilik nilai akhir",
    )
    final_score: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), nullable=False, comment="Nilai akhir terbobot pada skala seratus",
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=GradeStatus.DRAFT, server_default="draft", index=True,
        comment="Status nilai: draft atau finalized",
    )
    finalized_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Waktu finalisasi nilai",
    )
    finalized_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True, comment="Pengguna yang memfinalisasi nilai",
    )
    release_notified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="Waktu notifikasi rilis nilai terkirim",
    )
