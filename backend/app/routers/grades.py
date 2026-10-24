"""Class grade grids."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User
from app.schemas.grades import ClassGradesRead
from app.services.grade import class_grades

router = APIRouter(tags=["grades"])


@router.get("/classes/{class_id}/grades", response_model=ClassGradesRead)
async def get_class_grades(
    class_id: uuid.UUID, db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("superadmin", "lecturer")),
) -> ClassGradesRead:
    return await class_grades(db, class_id, user)
