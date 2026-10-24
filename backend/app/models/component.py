"""Grade components configured per class."""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class ComponentCategory(StrEnum):
    TUGAS = "tugas"
    UTS = "uts"
    UAS = "uas"
    CUSTOM = "custom"


class Component(Base):
    __tablename__ = "components"
    __table_args__ = (
        CheckConstraint("weight > 0 AND weight <= 100", name="ck_components_weight"),
        CheckConstraint("max_score > 0", name="ck_components_max_score"),
        CheckConstraint("category IN ('tugas', 'uts', 'uas', 'custom')", name="ck_components_category"),
        {"comment": "Tabel komponen penilaian per kelas"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
        comment="Identitas unik komponen penilaian",
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=False, index=True,
        comment="Kelas pemilik komponen penilaian",
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="Nama komponen penilaian")
    category: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Kategori: tugas, uts, uas, atau custom",
    )
    weight: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, comment="Bobot komponen dalam persen",
    )
    max_score: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), nullable=False, default=Decimal("100"), server_default="100",
        comment="Nilai maksimum komponen",
    )
    order_index: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0", comment="Urutan tampilan komponen",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        comment="Waktu pembuatan komponen penilaian",
    )
