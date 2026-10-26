"""Score entry endpoints.

Adapter HTTP penyimpanan skor yang didaftarkan app.main.

Dependency menetapkan identitas/role; aturan bisnis dan persistence
didelegasikan ke service.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User
from app.schemas.grades import GradeRead
from app.schemas.scores import ScorePayload
from app.services.scores import save_scores

router = APIRouter(tags=["scores"])


@router.put("/enrollments/{enrollment_id}/scores", response_model=GradeRead)
async def put_scores(
    enrollment_id: uuid.UUID, payload: ScorePayload,
    db: AsyncSession = Depends(get_db), user: User = Depends(require_role("superadmin", "lecturer")),
) -> GradeRead:
    """Simpan patch skor tanpa mengubah komponen yang tidak dikirim.

    \f

    Upsert numeric scores, clear null scores; omitted component scores
    are retained.

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        enrollment_id: UUID keikutsertaan mahasiswa pada satu kelas.
        payload: Data masukan yang sudah melewati validasi schema
            endpoint.
        db: Session database; batas commit mengikuti operasi terkait.
        user: Objek akun untuk pemeriksaan akses atau persistence sesuai
            operasi.

    Returns:
        Total draft beserta status dan metadata audit penilaian.
    """
    return GradeRead.model_validate(await save_scores(db, enrollment_id, payload, user))
