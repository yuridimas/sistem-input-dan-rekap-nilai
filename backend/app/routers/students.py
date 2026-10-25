"""Student management router."""

import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User
from app.schemas.student import StudentCreate, StudentRead, StudentUpdate
from app.services import student as student_service

router = APIRouter(prefix="/students", tags=["students"])


@router.post("", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
async def create_student(
    payload: StudentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "lecturer")),
) -> StudentRead:
    student = await student_service.create_student(db, payload)
    return StudentRead.model_validate(student)


@router.get("", response_model=list[StudentRead])
async def list_students(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "lecturer")),
) -> list[StudentRead]:
    students = await student_service.list_students(db)
    return [StudentRead.model_validate(student) for student in students]


@router.get("/{student_id}", response_model=StudentRead)
async def get_student(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "lecturer")),
) -> StudentRead:
    student = await student_service.get_student(db, student_id)
    return StudentRead.model_validate(student)


@router.patch("/{student_id}", response_model=StudentRead)
async def update_student(
    student_id: uuid.UUID,
    payload: StudentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin")),
) -> StudentRead:
    student = await student_service.update_student(db, student_id, payload)
    return StudentRead.model_validate(student)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin")),
) -> Response:
    await student_service.delete_student(db, student_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
