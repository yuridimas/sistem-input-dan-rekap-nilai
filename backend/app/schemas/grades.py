"""Draft grade and class grade grid responses.

Kontrak grid, hasil simpan, finalisasi, dan ranking untuk router
penilaian.

Batas field pada schema menjaga input; aturan relasi dan otorisasi tetap
berada di service.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.grade import GradeStatus
from app.schemas.component import ComponentRead
from app.schemas.student import StudentRead


class GradeRead(BaseModel):
    """Status dan audit rilis satu enrollment tanpa rincian skor."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    enrollment_id: uuid.UUID
    final_score: Decimal
    status: GradeStatus
    finalized_at: datetime | None
    finalized_by: uuid.UUID | None
    release_notified_at: datetime | None


class GradeRowRead(BaseModel):
    """Baris grid; total None mewakili draft yang belum diisi.

    Dict skor kosong menandai belum adanya entri komponen.
    """

    enrollment_id: uuid.UUID
    student: StudentRead
    scores: dict[uuid.UUID, Decimal]
    final_score: Decimal | None
    status: GradeStatus


class ClassGradesRead(BaseModel):
    """Snapshot konfigurasi kolom dan seluruh roster editor."""

    class_id: uuid.UUID
    components: list[ComponentRead]
    grades: list[GradeRowRead]


class FinalizeRead(BaseModel):
    """Jumlah nilai final dan task diterima, bukan email sampai.

    Angka notified tidak menyatakan bahwa email sudah diterima.
    """

    finalized_count: int
    notified: int


class RankingRead(BaseModel):
    """Posisi ranking tersimpan dengan mahasiswa dan total final."""

    rank: int
    enrollment_id: uuid.UUID
    student: StudentRead
    final_score: Decimal
