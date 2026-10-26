"""Stored sequential class rankings at grade release.

Snapshot ranking yang dibuat bersama finalisasi dan dibaca
history/reports.
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class Ranking(Base):
    """Posisi unik mahasiswa pada snapshot ranking kelas.

    Tie-break deterministik menghasilkan posisi unik, bukan ranking
    bersama.
    """

    __tablename__ = "rankings"
    __table_args__ = (
        UniqueConstraint("class_id", "enrollment_id", name="uq_rankings_class_enrollment"),
        UniqueConstraint("class_id", "rank", name="uq_rankings_class_rank"),
        CheckConstraint("rank > 0", name="ck_rankings_positive_rank"),
        {"comment": "Tabel peringkat kelas saat nilai difinalisasi"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="Identitas unik peringkat",
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False, index=True,
        comment="Kelas pemilik peringkat",
    )
    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("enrollments.id"), nullable=False, index=True,
        comment="Pendaftaran mahasiswa yang diberi peringkat",
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False, comment="Peringkat berurutan dalam kelas")
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        comment="Waktu penghitungan peringkat kelas",
    )
