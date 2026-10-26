"""Report data shared by PDF and XLSX rendering.

Data lepas ORM untuk renderer PDF dan XLSX pada service reports.

Batas field pada schema menjaga input; aturan relasi dan otorisasi tetap
berada di service.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ReportRow(BaseModel):
    """Baris nilai yang telah divalidasi final oleh service."""

    enrollment_id: uuid.UUID
    nim: str
    full_name: str
    final_score: Decimal
    rank: int | None
    finalized_at: datetime | None


class ReportComponent(BaseModel):
    """Konfigurasi kolom laporan; score dipakai saat laporan individu.
    """

    id: uuid.UUID
    name: str
    category: str
    weight: Decimal
    max_score: Decimal
    score: Decimal | None


class ReportData(BaseModel):
    """Konteks renderer dengan peta skor per enrollment."""

    class_id: uuid.UUID
    course_name: str
    course_code: str
    semester: str
    section: str
    academic_year: str
    rows: list[ReportRow]
    components: list[ReportComponent] = Field(default_factory=list)
    component_scores: dict[uuid.UUID, dict[uuid.UUID, Decimal | None]] = Field(default_factory=dict)
