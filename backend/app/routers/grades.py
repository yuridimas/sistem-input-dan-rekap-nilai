"""Class grade grids."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User
from app.schemas.grades import ClassGradesRead, FinalizeRead, RankingRead
from app.schemas.history import HistoryRead
from app.services.grade import class_grades, finalize_class
from app.services.ranking import class_ranking
from app.services.history import student_history

router = APIRouter(tags=["grades"])


@router.get("/classes/{class_id}/grades", response_model=ClassGradesRead)
async def get_class_grades(
    class_id: uuid.UUID, db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("superadmin", "lecturer")),
) -> ClassGradesRead:
    return await class_grades(db, class_id, user)


@router.post("/classes/{class_id}/finalize", response_model=FinalizeRead, status_code=202)
async def finalize_grades(
    class_id: uuid.UUID, db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("superadmin", "lecturer")),
) -> FinalizeRead:
    return await finalize_class(db, class_id, user)


@router.get("/classes/{class_id}/ranking", response_model=list[RankingRead])
async def get_ranking(
    class_id: uuid.UUID, db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("superadmin", "lecturer")),
) -> list[RankingRead]:
    return await class_ranking(db, class_id, user)


@router.get("/students/{student_id}/history", response_model=list[HistoryRead])
async def get_student_history(
    student_id: uuid.UUID, db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("superadmin", "lecturer")),
) -> list[HistoryRead]:
    return await student_history(db, student_id, user)
