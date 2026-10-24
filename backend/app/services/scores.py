"""Atomically validate, save scores, and update the draft final grade."""

import uuid
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.grade import Grade, GradeStatus
from app.models.user import User
from app.repositories import component as component_repo
from app.repositories import grades as grade_repo
from app.repositories import scores as score_repo
from app.schemas.component import ComponentCreate
from app.services.class_ import get_class
from app.services.component_rules import validate_configuration
from app.services.grade import calculate_final_score


async def save_scores(
    db: AsyncSession, enrollment_id: uuid.UUID, values: dict[uuid.UUID, Decimal], user: User,
) -> Grade:
    enrollment = await score_repo.get_enrollment(db, enrollment_id)
    if enrollment is None:
        raise HTTPException(404, "Pendaftaran mahasiswa tidak ditemukan")
    class_id = enrollment.class_id
    # Shared with component changes so calculation always uses the saved configuration.
    await component_repo.lock_class(db, class_id)
    await get_class(db, class_id, user)
    enrollment = await score_repo.get_enrollment(db, enrollment_id, lock=True)
    if enrollment is None:
        raise HTTPException(404, "Pendaftaran mahasiswa tidak ditemukan")
    grade = await grade_repo.get_by_enrollment(db, enrollment_id)
    if grade is not None and grade.status == GradeStatus.FINALIZED:
        raise HTTPException(409, "Nilai yang sudah difinalisasi tidak dapat diubah")
    components = await component_repo.list_by_class(db, class_id)
    validate_configuration([ComponentCreate.model_validate({
        "name": component.name, "category": component.category, "weight": component.weight,
        "max_score": component.max_score, "order_index": component.order_index,
    }) for component in components])
    by_id = {component.id: component for component in components}
    for component_id, value in values.items():
        if component_id not in by_id:
            raise HTTPException(422, "Komponen penilaian tidak ditemukan pada kelas ini")
        if value < 0 or value > by_id[component_id].max_score:
            raise HTTPException(422, "Nilai harus antara nol dan nilai maksimum komponen")
    try:
        await score_repo.upsert(db, enrollment_id, values, user.id)
        scores = {row.component_id: row.score for row in await score_repo.list_by_enrollment(db, enrollment_id)}
        final_score = calculate_final_score(components, scores)
        if grade is None:
            grade = grade_repo.add_draft(db, enrollment_id, final_score)
        else:
            grade.final_score = final_score
        await db.commit()
        await db.refresh(grade)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Data penilaian telah berubah; muat ulang dan coba kembali")
    return grade
