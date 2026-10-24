"""Ranking queries and inserts within the caller's transaction."""

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enrollment import Enrollment
from app.models.grade import Grade, GradeStatus
from app.models.ranking import Ranking
from app.models.student import Student


async def create_for_class(db: AsyncSession, class_id: uuid.UUID, computed_at: datetime) -> None:
    rows = (await db.execute(
        select(Enrollment.id, func.row_number().over(
            order_by=(Grade.final_score.desc(), Student.nim.asc(), Student.full_name.asc())
        ).label("rank"))
        .join(Grade, Grade.enrollment_id == Enrollment.id)
        .join(Student, Student.id == Enrollment.student_id)
        .where(Enrollment.class_id == class_id, Grade.status == GradeStatus.FINALIZED)
    )).all()
    db.add_all([
        Ranking(class_id=class_id, enrollment_id=row.id, rank=row.rank, computed_at=computed_at)
        for row in rows
    ])
    await db.flush()


async def list_by_class(db: AsyncSession, class_id: uuid.UUID) -> list[tuple[Ranking, Student, Grade]]:
    result = await db.execute(
        select(Ranking, Student, Grade)
        .join(Enrollment, Enrollment.id == Ranking.enrollment_id)
        .join(Student, Student.id == Enrollment.student_id)
        .join(Grade, Grade.enrollment_id == Enrollment.id)
        .where(Ranking.class_id == class_id).order_by(Ranking.rank)
    )
    return list(result.all())
