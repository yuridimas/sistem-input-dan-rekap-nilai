"""Class model.

Relasi kelas ke mata kuliah dan dosen untuk pembatasan akses dan roster.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class Class(Base):
    """Seksi per mata kuliah/tahun; kombinasi unik mencegah kelas ganda.
    """

    __tablename__ = "classes"
    __table_args__ = (
        UniqueConstraint(
            "course_id",
            "section",
            "academic_year",
            name="uq_classes_course_section_academic_year",
        ),
        {
            "comment": "Tabel kelas (seksi mata kuliah yang diampu dosen)",
        },
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Identitas unik kelas",
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id"),
        nullable=False,
        index=True,
        comment="Mata kuliah yang diajarkan pada kelas ini",
    )
    section: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Kelas/seksi (mis. A, B)",
    )
    lecturer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="Dosen pengampu kelas",
    )
    academic_year: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Tahun akademik (mis. 2026/2027)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Waktu pembuatan data kelas",
    )
