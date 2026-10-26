"""Business logic for course management.

Aturan kepemilikan dan kode unik mata kuliah bagi router courses.

Dosen kelas terkait mendapat hak baca; mutasi tetap dibatasi
pencipta/superadmin.
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course
from app.models.user import User, UserRole
from app.repositories import course as course_repo
from app.schemas.course import CourseCreate, CourseUpdate


def _is_superadmin(user: User) -> bool:
    """Kenali pengguna yang boleh mengelola mata kuliah lintas pencipta.

    Args:
        user: Objek akun untuk pemeriksaan akses atau persistence sesuai
            operasi.
    """
    return str(user.role) == UserRole.SUPERADMIN.value


async def create_course(
    db: AsyncSession,
    payload: CourseCreate,
    current_user: User,
) -> Course:
    """Cegah kode ganda sebelum mencatat pencipta mata kuliah.

    Commit DB.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        payload: Data masukan yang sudah melewati validasi schema
            endpoint.
        current_user: Akun aktif pemanggil sebagai dasar pemeriksaan
            akses.

    Raises:
        HTTPException: 409 jika kode sudah digunakan.
    """
    existing = await course_repo.get_by_code(db, payload.code)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Kode mata kuliah sudah terdaftar",
        )
    course = Course(
        code=payload.code,
        name=payload.name,
        credits=payload.credits,
        semester=payload.semester,
        created_by=current_user.id,
    )
    return await _add_or_conflict(db, course)


async def list_courses(db: AsyncSession, current_user: User) -> list[Course]:
    """Sertakan mata kuliah buatan pengguna atau penugasannya.

    Daftar bisa kosong, hanya membaca DB.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        current_user: Akun aktif pemanggil sebagai dasar pemeriksaan
            akses.

    Returns:
        Daftar mata kuliah buatan pengguna atau penugasannya; superadmin
        tidak dibatasi filter pencipta.
    """
    created_by = None if _is_superadmin(current_user) else current_user.id
    return await course_repo.list_courses(db, created_by=created_by)


async def get_course(
    db: AsyncSession,
    course_id: uuid.UUID,
    current_user: User,
) -> Course:
    """Izinkan baca bagi pencipta, dosen penugasan, atau superadmin.

    Hanya membaca DB.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        course_id: UUID mata kuliah yang menjadi sasaran operasi.
        current_user: Akun aktif pemanggil sebagai dasar pemeriksaan
            akses.

    Raises:
        HTTPException: 404 jika absen, 403 jika tidak berhak.
    """
    course = await course_repo.get_by_id(db, course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mata kuliah tidak ditemukan",
        )
    if (not _is_superadmin(current_user) and course.created_by != current_user.id
            and not await course_repo.has_assigned_class(db, course.id, current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Anda tidak memiliki akses ke mata kuliah ini",
        )
    return course


async def _get_writable_course(db: AsyncSession, course_id: uuid.UUID, current_user: User) -> Course:
    """Pisahkan hak baca dosen penugasan dari hak ubah pencipta/admin.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        course_id: UUID mata kuliah yang menjadi sasaran operasi.
        current_user: Akun aktif pemanggil sebagai dasar pemeriksaan
            akses.

    Raises:
        HTTPException: 403/404 jika tidak berhak atau data absen.
    """
    course = await get_course(db, course_id, current_user)
    if not _is_superadmin(current_user) and course.created_by != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Hanya pembuat atau superadmin yang dapat mengubah mata kuliah")
    return course


async def update_course(
    db: AsyncSession,
    course_id: uuid.UUID,
    payload: CourseUpdate,
    current_user: User,
) -> Course:
    """Periksa hak ubah dan kode unik sebelum menerapkan patch.

    Commit DB.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        course_id: UUID mata kuliah yang menjadi sasaran operasi.
        payload: Data masukan yang sudah melewati validasi schema
            endpoint.
        current_user: Akun aktif pemanggil sebagai dasar pemeriksaan
            akses.

    Raises:
        HTTPException: 403/404 akses atau 409 duplikasi kode.
    """
    course = await _get_writable_course(db, course_id, current_user)

    if payload.code is not None and payload.code != course.code:
        existing = await course_repo.get_by_code(db, payload.code)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Kode mata kuliah sudah terdaftar",
            )
        course.code = payload.code

    if payload.name is not None:
        course.name = payload.name
    if payload.credits is not None:
        course.credits = payload.credits
    if payload.semester is not None:
        course.semester = payload.semester

    try:
        return await course_repo.save(db, course)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Kode mata kuliah sudah terdaftar",
        )


async def delete_course(
    db: AsyncSession,
    course_id: uuid.UUID,
    current_user: User,
) -> None:
    """Hapus hanya bila pengguna berhak dan relasi tidak menghalangi.

    Commit DB.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        course_id: UUID mata kuliah yang menjadi sasaran operasi.
        current_user: Akun aktif pemanggil sebagai dasar pemeriksaan
            akses.

    Raises:
        HTTPException: 403/404 akses atau 409 constraint relasi.
    """
    course = await _get_writable_course(db, course_id, current_user)
    try:
        await course_repo.delete(db, course)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Mata kuliah masih memiliki kelas dan tidak dapat dihapus",
        )


async def _add_or_conflict(db: AsyncSession, course: Course) -> Course:
    """Terjemahkan konflik insert paralel menjadi error kode duplikat.

    Commit DB.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        course: Objek mata kuliah yang dilacak session.

    Raises:
        HTTPException: Rollback dan HTTPException 409 pada
            IntegrityError.
    """
    try:
        return await course_repo.add(db, course)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Kode mata kuliah sudah terdaftar",
        )
