"""Authorized access to stored class ranking snapshots."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories import ranking as ranking_repo
from app.schemas.grades import RankingRead
from app.schemas.student import StudentRead
from app.services.class_ import get_class


async def class_ranking(db: AsyncSession, class_id: uuid.UUID, user: User) -> list[RankingRead]:
    await get_class(db, class_id, user)
    return [RankingRead(
        rank=ranking.rank, enrollment_id=ranking.enrollment_id,
        student=StudentRead.model_validate(student), final_score=grade.final_score,
    ) for ranking, student, grade in await ranking_repo.list_by_class(db, class_id)]
