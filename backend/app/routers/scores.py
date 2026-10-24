"""Score entry endpoints."""

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
    """Upsert the supplied scores; omitted component scores are retained."""
    return GradeRead.model_validate(await save_scores(db, enrollment_id, payload, user))
