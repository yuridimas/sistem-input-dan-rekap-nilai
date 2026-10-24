"""Course management router."""

import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.user import User
from app.schemas.course import CourseCreate, CourseRead, CourseUpdate
from app.services import course as course_service

router = APIRouter(prefix="/courses", tags=["courses"])


@router.post("", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
async def create_course(
    payload: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "lecturer")),
) -> CourseRead:
    course = await course_service.create_course(db, payload, current_user)
    return CourseRead.model_validate(course)


@router.get("", response_model=list[CourseRead])
async def list_courses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CourseRead]:
    courses = await course_service.list_courses(db, current_user)
    return [CourseRead.model_validate(course) for course in courses]


@router.get("/{course_id}", response_model=CourseRead)
async def get_course(
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CourseRead:
    course = await course_service.get_course(db, course_id, current_user)
    return CourseRead.model_validate(course)


@router.patch("/{course_id}", response_model=CourseRead)
async def update_course(
    course_id: uuid.UUID,
    payload: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CourseRead:
    course = await course_service.update_course(db, course_id, payload, current_user)
    return CourseRead.model_validate(course)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    await course_service.delete_course(db, course_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
