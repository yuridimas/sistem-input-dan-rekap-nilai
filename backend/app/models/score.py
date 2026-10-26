"""Per-component scores and entry audit metadata.

Skor mentah komponen yang menjadi masukan kalkulasi service grade.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class Score(Base):
    """Skor unik per enrollment dan komponen penilaian.

    Maksimum skor bergantung komponen dan diperiksa service scores.
    """

    __tablename__ = "scores"
    __table_args__ = (
        UniqueConstraint("enrollment_id", "component_id", name="uq_scores_enrollment_component"),
        CheckConstraint("score >= 0", name="ck_scores_nonnegative"),
        {"comment": "Tabel nilai mahasiswa per komponen penilaian"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="Identitas unik nilai komponen",
    )
    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("enrollments.id"), nullable=False, index=True,
        comment="Pendaftaran mahasiswa pemilik nilai",
    )
    component_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("components.id"), nullable=False, index=True,
        comment="Komponen penilaian yang dinilai",
    )
    score: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), nullable=False, comment="Nilai yang diperoleh mahasiswa",
    )
    entered_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True,
        comment="Pengguna yang terakhir memasukkan nilai",
    )
    entered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.clock_timestamp(),
        comment="Waktu nilai pertama kali dimasukkan",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.clock_timestamp(),
        onupdate=func.clock_timestamp(), comment="Waktu pembaruan nilai terakhir",
    )
