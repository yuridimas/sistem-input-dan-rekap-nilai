"""Persistent grade-release delivery status, one record per grade."""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class NotificationStatus(StrEnum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        CheckConstraint("status IN ('queued', 'sent', 'failed')", name="ck_notifications_status"),
        {"comment": "Tabel status pengiriman notifikasi rilis nilai"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="Identitas unik notifikasi",
    )
    grade_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("grades.id"), nullable=False, unique=True, index=True,
        comment="Nilai akhir yang diberitahukan kepada mahasiswa",
    )
    dispatch_token: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, default=uuid.uuid4, server_default=func.gen_random_uuid(),
        comment="Token pengantrean untuk mengabaikan hasil percobaan yang sudah digantikan",
    )
    student_email: Mapped[str | None] = mapped_column(
        String(255), comment="Alamat email tujuan; kosong bila mahasiswa belum memiliki email",
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=NotificationStatus.QUEUED, server_default="queued", index=True,
        comment="Status pengiriman: queued, sent, atau failed",
    )
    error_message: Mapped[str | None] = mapped_column(Text, comment="Pesan kegagalan pengiriman terakhir")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="Waktu notifikasi berhasil dikirim")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), comment="Waktu pembuatan notifikasi",
    )
