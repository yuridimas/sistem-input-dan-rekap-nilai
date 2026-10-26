"""Business logic for class and enrollment management.

Aturan kepemilikan kelas dan perubahan roster untuk router classes.

Lock kelas menyelaraskan perubahan roster dengan penilaian dan
finalisasi.
"""

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
from app.repositories import component as component_repo
from app.repositories import enrollment as enrollment_repo
from app.repositories import grades as grade_repo
from app.repositories import student as student_repo
from app.repositories import user as user_repo
from app.schemas.class_ import ClassCreate, ClassRead, ClassUpdate, EnrollmentCreate


def _is_superadmin(user: User) -> bool:
    """Bedakan hak lintas dosen dari akses milik sendiri.

    Args:
        user: Objek akun untuk pemeriksaan akses atau persistence sesuai
            operasi.
    """
    return str(user.role) == UserRole.SUPERADMIN.value


async def _validate_lecturer(db: AsyncSession, lecturer_id: uuid.UUID) -> None:
    """Pastikan penugasan kelas menunjuk pengguna dengan role dosen.

    Hanya membaca DB.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        lecturer_id: UUID akun yang harus ada dan memiliki role
            lecturer.

    Raises:
        HTTPException: 404 jika absen, 422 jika role salah.
    """
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
    """Tetapkan pemilik sesuai role dan cegah duplikasi seksi/tahun.

    Commit DB.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        payload: Kontrak kelas; penugasan lecturer_id ditafsirkan sesuai
            role.
        current_user: Akun aktif pemanggil sebagai dasar pemeriksaan
            akses.

    Raises:
        HTTPException: 403/404/422 akses/input, 409 duplikasi.
    """
    course = await course_repo.get_by_id(db, payload.course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mata kuliah tidak ditemukan",
        )

    # Dosen membuat kelas untuk dirinya; hanya superadmin yang dapat menunjuk dosen lain.
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
    """Batasi kelas pada dosen pemilik; admin melihat semua.

    Hanya membaca DB.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        current_user: Akun aktif pemanggil sebagai dasar pemeriksaan
            akses.

    Returns:
        Daftar bisa kosong.
    """
    lecturer_id = None if _is_superadmin(current_user) else current_user.id
    return await class_repo.list_classes(db, lecturer_id=lecturer_id)


async def serialize_classes(db: AsyncSession, classes: list[Class]) -> list[ClassRead]:
    """Tambahkan status penguncian finalisasi secara batch untuk UI.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        classes: Objek kelas yang akan dilengkapi status finalisasinya.
    """
    locked_ids = await class_repo.finalized_class_ids(db, [row.id for row in classes])
    return [ClassRead.model_validate(row).model_copy(update={
        "has_finalized_grades": row.id in locked_ids,
    }) for row in classes]


async def get_class(
    db: AsyncSession,
    class_id: uuid.UUID,
    current_user: User,
) -> Class:
    """Jadikan pemeriksaan kelas sebagai batas otorisasi service lain.

    Hanya membaca DB.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        class_id: UUID kelas yang menjadi cakupan operasi.
        current_user: Akun aktif pemanggil sebagai dasar pemeriksaan
            akses.

    Raises:
        HTTPException: 404 jika absen, 403 jika bukan pemilik.
    """
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
    """Validasi penugasan dosen dan kombinasi unik sebelum perubahan.

    Commit DB.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        class_id: UUID kelas yang menjadi cakupan operasi.
        payload: Data masukan yang sudah melewati validasi schema
            endpoint.
        current_user: Akun aktif pemanggil sebagai dasar pemeriksaan
            akses.

    Raises:
        HTTPException: 403/404/422/409 untuk akses, input, atau konflik.
    """
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
    """Hapus kelas yang diizinkan dan tidak terhalang relasi mahasiswa.

    Commit DB.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        class_id: UUID kelas yang menjadi cakupan operasi.
        current_user: Akun aktif pemanggil sebagai dasar pemeriksaan
            akses.

    Raises:
        HTTPException: 403/404 akses, 409 jika constraint menolak.
    """
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
    """Daftarkan mahasiswa dengan memakai ulang NIM yang sudah ada.

    Lock/commit DB.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        class_id: UUID kelas yang menjadi cakupan operasi.
        payload: Data masukan yang sudah melewati validasi schema
            endpoint.
        current_user: Akun aktif pemanggil sebagai dasar pemeriksaan
            akses.

    Raises:
        HTTPException: 403/404/409 akses, kelas final, atau duplikasi.
    """
    class_ = await _lock_mutable_roster(db, class_id, current_user)
    class_pk = class_.id

    try:
        student = await student_repo.get_or_create_for_enrollment(db, Student(
            nim=payload.nim,
            full_name=payload.full_name or payload.nim,
            email=payload.email,
        ))
        existing = await enrollment_repo.get_by_class_and_student(db, class_pk, student.id)
        if existing is not None:
            raise HTTPException(409, "Mahasiswa sudah terdaftar di kelas ini")
        enrollment = Enrollment(class_id=class_pk, student_id=student.id)
        enrollment = await enrollment_repo.add(db, enrollment)
        await db.commit()
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
    """Baca pasangan enrollment/mahasiswa setelah otorisasi.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        class_id: UUID kelas yang menjadi cakupan operasi.
        current_user: Akun aktif pemanggil sebagai dasar pemeriksaan
            akses.

    Returns:
        Daftar bisa kosong.

    Raises:
        HTTPException: 403/404 jika akses kelas gagal.
    """
    class_ = await get_class(db, class_id, current_user)
    return await enrollment_repo.list_by_class(db, class_.id)


async def delete_enrollment(
    db: AsyncSession,
    class_id: uuid.UUID,
    enrollment_id: uuid.UUID,
    current_user: User,
) -> None:
    """Hapus enrollment kelas tujuan hanya ketika roster boleh diubah.

    Lock/commit DB.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        class_id: UUID kelas yang menjadi cakupan operasi.
        enrollment_id: UUID keikutsertaan mahasiswa pada satu kelas.
        current_user: Akun aktif pemanggil sebagai dasar pemeriksaan
            akses.

    Raises:
        HTTPException: 403/404/409 akses, final, atau relasi nilai.
    """
    class_ = await _lock_mutable_roster(db, class_id, current_user)
    class_pk = class_.id
    enrollment = await enrollment_repo.get_by_id(db, enrollment_id)
    if enrollment is None or enrollment.class_id != class_pk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pendaftaran tidak ditemukan pada kelas ini",
        )
    try:
        await enrollment_repo.delete(db, enrollment)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pendaftaran masih memiliki nilai dan tidak dapat dihapus",
        )


async def _lock_mutable_roster(db: AsyncSession, class_id: uuid.UUID, user: User) -> Class:
    """Kunci kelas dan pastikan roster masih boleh diubah.

    Lock hingga akhir transaksi.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        class_id: UUID kelas yang menjadi cakupan operasi.
        user: Objek akun untuk pemeriksaan akses atau persistence sesuai
            operasi.

    Raises:
        HTTPException: 403/404 akses atau 409 kelas final.
    """
    await component_repo.lock_class(db, class_id)
    class_ = await get_class(db, class_id, user)
    if await grade_repo.has_finalized_class(db, class_id):
        raise HTTPException(409, "Daftar mahasiswa kelas yang sudah difinalisasi tidak dapat diubah")
    return class_
