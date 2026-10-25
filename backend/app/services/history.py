"""Assemble authorized finalized history without modifying released data."""

import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.repositories import history as history_repo
from app.repositories import student as student_repo
from app.schemas.history import HistoryClassRead, HistoryComponentRead, HistoryCourseRead, HistoryRead


async def student_history(db: AsyncSession, student_id: uuid.UUID, user: User) -> list[HistoryRead]:
    if await student_repo.get_by_id(db, student_id) is None:
        raise HTTPException(404, "Mahasiswa tidak ditemukan")
    lecturer_id = None if str(user.role) == UserRole.SUPERADMIN.value else user.id
    rows = await history_repo.list_finalized(db, student_id, lecturer_id)
    details: dict[uuid.UUID, list[HistoryComponentRead]] = {}
    for enrollment_id, component, score in await history_repo.list_components(
        db, [enrollment.id for _grade, enrollment, _course, _class, _rank in rows],
    ):
        details.setdefault(enrollment_id, []).append(HistoryComponentRead(
            id=component.id, name=component.name, category=component.category,
            weight=component.weight, max_score=component.max_score,
            order_index=component.order_index, score=score,
        ))
    return [HistoryRead(
        grade_id=grade.id, enrollment_id=enrollment.id,
        course=HistoryCourseRead.model_validate(course), class_=HistoryClassRead.model_validate(class_),
        final_score=grade.final_score, rank=rank, finalized_at=grade.finalized_at,
        components=details.get(enrollment.id, []),
    ) for grade, enrollment, course, class_, rank in rows]
