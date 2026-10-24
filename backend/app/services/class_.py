"""Business logic for class and enrollment management."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.class_ import Class
from app.models.enrollment import Enrollment
from app.models.student import Student
from app.models.user import User, UserRole
from app.repositories import class_ as class_repo
from app.repositories import course as course_repo
from app.repositories import enrollment as enrollment_repo
from app.repositories import student as student_repo
from app.repositories import user as user_repo
from app.schemas.class_ import ClassCreate, ClassUpdate, EnrollmentCreate


def _is_superadmin(user: User) -> bool:
    return str(user.role) == UserRole.SUPERADMIN.value


async def _validate_lecturer(db: AsyncSession, lecturer_id: uuid.UUID) -> None:
    lecturer = await user_repo.get_by_id(db, lecturer_id)
    if lecturer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dosen tidak ditemukan",
        )
    if str(lecturer.role) != UserRole.LECTURER.value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Pengguna yang dipilih bukan dosen",
        )


async def create_class(
    db: AsyncSession,
    payload: ClassCreate,
    current_user: User,
) -> Class:
    course = await course_repo.get_by_id(db, payload.course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mata kuliah tidak ditemukan",
        )

    if _is_superadmin(current_user):
        if payload.lecturer_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="lecturer_id wajib diisi untuk superadmin",
            )
        lecturer_id = payload.lecturer_id
        await _validate_lecturer(db, lecturer_id)
    else:
        if payload.lecturer_id is not None and payload.lecturer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Dosen hanya dapat membuat kelas untuk dirinya sendiri",
            )
        lecturer_id = current_user.id

    existing = await class_repo.get_by_unique(
        db,
        payload.course_id,
        payload.section,
        payload.academic_year,
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Kelas dengan seksi dan tahun akademik tersebut sudah terdaftar",
        )

    class_ = Class(
        course_id=payload.course_id,
        section=payload.section,
        lecturer_id=lecturer_id,
        academic_year=payload.academic_year,
    )
    try:
        return await class_repo.add(db, class_)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Kelas dengan seksi dan tahun akademik tersebut sudah terdaftar",
        )


async def list_classes(db: AsyncSession, current_user: User) -> list[Class]:
    lecturer_id = None if _is_superadmin(current_user) else current_user.id
    return await class_repo.list_classes(db, lecturer_id=lecturer_id)


async def get_class(
    db: AsyncSession,
    class_id: uuid.UUID,
    current_user: User,
) -> Class:
    class_ = await class_repo.get_by_id(db, class_id)
    if class_ is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kelas tidak ditemukan",
        )
    if not _is_superadmin(current_user) and class_.lecturer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anda tidak memiliki akses ke kelas ini",
        )
    return class_


async def update_class(
    db: AsyncSession,
    class_id: uuid.UUID,
    payload: ClassUpdate,
    current_user: User,
) -> Class:
    class_ = await get_class(db, class_id, current_user)

    if payload.lecturer_id is not None:
        if not _is_superadmin(current_user):
            if payload.lecturer_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Dosen hanya dapat mengelola kelas miliknya sendiri",
                )
        else:
            await _validate_lecturer(db, payload.lecturer_id)
            class_.lecturer_id = payload.lecturer_id

    new_section = payload.section if payload.section is not None else class_.section
    new_academic_year = (
        payload.academic_year
        if payload.academic_year is not None
        else class_.academic_year
    )
    if new_section != class_.section or new_academic_year != class_.academic_year:
        existing = await class_repo.get_by_unique(
            db,
            class_.course_id,
            new_section,
            new_academic_year,
            exclude_id=class_.id,
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Kelas dengan seksi dan tahun akademik tersebut sudah terdaftar",
            )
        class_.section = new_section
        class_.academic_year = new_academic_year

    try:
        return await class_repo.save(db, class_)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Kelas dengan seksi dan tahun akademik tersebut sudah terdaftar",
        )


async def delete_class(
    db: AsyncSession,
    class_id: uuid.UUID,
    current_user: User,
) -> None:
    class_ = await get_class(db, class_id, current_user)
    try:
        await class_repo.delete(db, class_)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Kelas masih memiliki mahasiswa dan tidak dapat dihapus",
        )


async def enroll_student(
    db: AsyncSession,
    class_id: uuid.UUID,
    payload: EnrollmentCreate,
    current_user: User,
) -> tuple[Enrollment, Student]:
    class_ = await get_class(db, class_id, current_user)

    student = await student_repo.get_by_nim(db, payload.nim)
    if student is not None:
        existing = await enrollment_repo.get_by_class_and_student(
            db, class_.id, student.id
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Mahasiswa sudah terdaftar di kelas ini",
            )
    else:
        student = Student(
            nim=payload.nim,
            full_name=payload.full_name or payload.nim,
            email=payload.email,
        )
        try:
            student = await student_repo.add(db, student)
        except IntegrityError:
            await db.rollback()
            student = await student_repo.get_by_nim(db, payload.nim)
            if student is None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="NIM sudah terdaftar",
                )

    enrollment = Enrollment(class_id=class_.id, student_id=student.id)
    try:
        enrollment = await enrollment_repo.add(db, enrollment)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Mahasiswa sudah terdaftar di kelas ini",
        )
    return enrollment, student


async def get_roster(
    db: AsyncSession,
    class_id: uuid.UUID,
    current_user: User,
) -> list[tuple[Enrollment, Student]]:
    class_ = await get_class(db, class_id, current_user)
    return await enrollment_repo.list_by_class(db, class_.id)


async def delete_enrollment(
    db: AsyncSession,
    class_id: uuid.UUID,
    enrollment_id: uuid.UUID,
    current_user: User,
) -> None:
    class_ = await get_class(db, class_id, current_user)
    enrollment = await enrollment_repo.get_by_id(db, enrollment_id)
    if enrollment is None or enrollment.class_id != class_.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pendaftaran tidak ditemukan pada kelas ini",
        )
    await enrollment_repo.delete(db, enrollment)
