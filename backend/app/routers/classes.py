"""Class, enrollment, and roster router."""

import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.enrollment import Enrollment
from app.models.student import Student
from app.models.user import User
from app.schemas.class_ import (
    ClassCreate,
    ClassRead,
    ClassUpdate,
    EnrollmentCreate,
    RosterEntryRead,
)
from app.schemas.student import StudentRead
from app.services import class_ as class_service

router = APIRouter(prefix="/classes", tags=["classes"])

_roles = require_role("superadmin", "lecturer")


def _roster_entry(enrollment: Enrollment, student: Student) -> RosterEntryRead:
    return RosterEntryRead(
        id=enrollment.id,
        enrolled_at=enrollment.enrolled_at,
        student=StudentRead.model_validate(student),
    )


@router.post("", response_model=ClassRead, status_code=status.HTTP_201_CREATED)
async def create_class(
    payload: ClassCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_roles),
) -> ClassRead:
    class_ = await class_service.create_class(db, payload, current_user)
    return (await class_service.serialize_classes(db, [class_]))[0]


@router.get("", response_model=list[ClassRead])
async def list_classes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_roles),
) -> list[ClassRead]:
    classes = await class_service.list_classes(db, current_user)
    return await class_service.serialize_classes(db, classes)


@router.get("/{class_id}", response_model=ClassRead)
async def get_class(
    class_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_roles),
) -> ClassRead:
    class_ = await class_service.get_class(db, class_id, current_user)
    return (await class_service.serialize_classes(db, [class_]))[0]


@router.patch("/{class_id}", response_model=ClassRead)
async def update_class(
    class_id: uuid.UUID,
    payload: ClassUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_roles),
) -> ClassRead:
    class_ = await class_service.update_class(db, class_id, payload, current_user)
    return (await class_service.serialize_classes(db, [class_]))[0]


@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class(
    class_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_roles),
) -> Response:
    await class_service.delete_class(db, class_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{class_id}/enrollments",
    response_model=RosterEntryRead,
    status_code=status.HTTP_201_CREATED,
)
async def enroll_student(
    class_id: uuid.UUID,
    payload: EnrollmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_roles),
) -> RosterEntryRead:
    enrollment, student = await class_service.enroll_student(
        db, class_id, payload, current_user
    )
    return _roster_entry(enrollment, student)


@router.get("/{class_id}/roster", response_model=list[RosterEntryRead])
async def get_roster(
    class_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_roles),
) -> list[RosterEntryRead]:
    rows = await class_service.get_roster(db, class_id, current_user)
    return [_roster_entry(enrollment, student) for enrollment, student in rows]


@router.delete(
    "/{class_id}/enrollments/{enrollment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_enrollment(
    class_id: uuid.UUID,
    enrollment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_roles),
) -> Response:
    await class_service.delete_enrollment(db, class_id, enrollment_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
