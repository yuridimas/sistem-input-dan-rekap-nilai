"""Decimal grade calculation and roster response assembly."""

import uuid
from decimal import Decimal
from fractions import Fraction

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.component import Component
from app.models.grade import GradeStatus
from app.models.user import User
from app.repositories import component as component_repo
from app.repositories import enrollment as enrollment_repo
from app.repositories import grades as grade_repo
from app.repositories import scores as score_repo
from app.schemas.component import ComponentRead
from app.schemas.grades import ClassGradesRead, GradeRowRead
from app.schemas.student import StudentRead
from app.services.class_ import get_class


def calculate_final_score(components: list[Component], scores: dict[uuid.UUID, Decimal]) -> Decimal:
    # Missing scores contribute zero; retain full class weights for partial drafts.
    # Normalize exactly so repeating divisions cannot move a half-cent below its boundary.
    total = sum((
        Fraction(scores.get(component.id, Decimal("0"))) * Fraction(component.weight) / Fraction(component.max_score)
        for component in components
    ), Fraction(0))
    cents = total * 100
    whole, remainder = divmod(cents.numerator, cents.denominator)
    if remainder * 2 >= cents.denominator:
        whole += 1
    return Decimal(whole).scaleb(-2)


async def ensure_components_mutable(db: AsyncSession, class_id: uuid.UUID) -> None:
    if any(grade.status == GradeStatus.FINALIZED for grade in await grade_repo.list_by_class(db, class_id)):
        raise HTTPException(409, "Komponen kelas dengan nilai final tidak dapat diubah")


async def validate_score_compatibility(
    db: AsyncSession, class_id: uuid.UUID, maximums: dict[uuid.UUID, Decimal],
) -> None:
    for score in await score_repo.list_by_class(db, class_id):
        if score.component_id not in maximums:
            raise HTTPException(409, "Komponen yang sudah memiliki nilai tidak dapat dihapus")
        if score.score > maximums[score.component_id]:
            raise HTTPException(422, "Nilai maksimum tidak boleh lebih kecil dari nilai yang tersimpan")


async def recalculate_class_drafts(db: AsyncSession, class_id: uuid.UUID) -> None:
    components = await component_repo.list_by_class(db, class_id)
    scores: dict[uuid.UUID, dict[uuid.UUID, Decimal]] = {}
    for score in await score_repo.list_by_class(db, class_id):
        scores.setdefault(score.enrollment_id, {})[score.component_id] = score.score
    for grade in await grade_repo.list_by_class(db, class_id):
        if grade.status == GradeStatus.DRAFT:
            grade.final_score = calculate_final_score(components, scores.get(grade.enrollment_id, {}))


async def class_grades(db: AsyncSession, class_id: uuid.UUID, user: User) -> ClassGradesRead:
    await get_class(db, class_id, user)
    components = await component_repo.list_by_class(db, class_id)
    roster = await enrollment_repo.list_by_class(db, class_id)
    grades = {grade.enrollment_id: grade for grade in await grade_repo.list_by_class(db, class_id)}
    score_maps: dict[uuid.UUID, dict[uuid.UUID, Decimal]] = {}
    for score in await score_repo.list_by_class(db, class_id):
        score_maps.setdefault(score.enrollment_id, {})[score.component_id] = score.score
    rows = []
    for enrollment, student in roster:
        grade = grades.get(enrollment.id)
        rows.append(GradeRowRead(
            enrollment_id=enrollment.id, student=StudentRead.model_validate(student),
            scores=score_maps.get(enrollment.id, {}), final_score=grade.final_score if grade else None,
            status=grade.status if grade else GradeStatus.DRAFT,
        ))
    return ClassGradesRead(
        class_id=class_id, components=[ComponentRead.model_validate(row) for row in components], grades=rows,
    )
