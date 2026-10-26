"""Authorized access to stored class ranking snapshots.

Pembacaan snapshot ranking oleh router grades setelah pemeriksaan akses
kelas.

Urutan peringkat dibuat saat finalisasi, bukan dihitung ulang oleh
endpoint pembacaan.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories import ranking as ranking_repo
from app.schemas.grades import RankingRead
from app.schemas.student import StudentRead
from app.services.class_ import get_class


async def class_ranking(db: AsyncSession, class_id: uuid.UUID, user: User) -> list[RankingRead]:
    """Sajikan ranking tersimpan setelah pemeriksaan akses kelas.

    Hanya membaca database.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        class_id: UUID kelas yang menjadi cakupan operasi.
        user: Objek akun untuk pemeriksaan akses atau persistence sesuai
            operasi.

    Returns:
        List[RankingRead], bisa kosong.

    Raises:
        HTTPException: 403/404 dari get_class.
    """
    await get_class(db, class_id, user)
    return [RankingRead(
        rank=ranking.rank, enrollment_id=ranking.enrollment_id,
        student=StudentRead.model_validate(student), final_score=grade.final_score,
    ) for ranking, student, grade in await ranking_repo.list_by_class(db, class_id)]
