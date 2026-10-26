"""Class, enrollment, and roster router.

Adapter HTTP kelas dan roster yang didaftarkan app.main.

Dependency menetapkan identitas/role; aturan bisnis dan persistence
didelegasikan ke service.
"""

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
    """Susun respons roster dari pasangan objek ORM.

    Serialisasi tidak memicu lazy-load relasi ORM.

    Args:
        enrollment: Objek keikutsertaan mahasiswa yang dilacak session.
        student: Objek profil mahasiswa yang dilacak session.
    """
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
    """Buat kelas dengan penugasan dosen sesuai hak pengguna.

    \f

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        payload: Kontrak kelas; penugasan lecturer_id ditafsirkan sesuai
            role.
        db: Session database; batas commit mengikuti operasi terkait.
        current_user: Akun aktif pemanggil sebagai dasar pemeriksaan
            akses.

    Returns:
        Metadata kelas baru beserta status penguncian.
    """
    class_ = await class_service.create_class(db, payload, current_user)
    return (await class_service.serialize_classes(db, [class_]))[0]


@router.get("", response_model=list[ClassRead])
async def list_classes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_roles),
) -> list[ClassRead]:
    """Sajikan kelas dan status finalisasi sesuai cakupan pengguna.

    \f

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        current_user: Akun aktif pemanggil sebagai dasar pemeriksaan
            akses.

    Returns:
        Daftar kelas yang terlihat oleh pengguna; bisa kosong.
    """
    classes = await class_service.list_classes(db, current_user)
    return await class_service.serialize_classes(db, classes)


@router.get("/{class_id}", response_model=ClassRead)
async def get_class(
    class_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_roles),
) -> ClassRead:
    """Sajikan metadata/status kelas setelah service memeriksa pemilik.

    \f

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        class_id: UUID kelas yang menjadi cakupan operasi.
        db: Session database; batas commit mengikuti operasi terkait.
        current_user: Akun aktif pemanggil sebagai dasar pemeriksaan
            akses.

    Returns:
        Metadata kelas beserta status penguncian.
    """
    class_ = await class_service.get_class(db, class_id, current_user)
    return (await class_service.serialize_classes(db, [class_]))[0]


@router.patch("/{class_id}", response_model=ClassRead)
async def update_class(
    class_id: uuid.UUID,
    payload: ClassUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_roles),
) -> ClassRead:
    """Ubah metadata kelas setelah validasi penugasan dan keunikan.

    \f

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        class_id: UUID kelas yang menjadi cakupan operasi.
        payload: Data masukan yang sudah melewati validasi schema
            endpoint.
        db: Session database; batas commit mengikuti operasi terkait.
        current_user: Akun aktif pemanggil sebagai dasar pemeriksaan
            akses.

    Returns:
        Metadata kelas terbaru beserta status penguncian.
    """
    class_ = await class_service.update_class(db, class_id, payload, current_user)
    return (await class_service.serialize_classes(db, [class_]))[0]


@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class(
    class_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_roles),
) -> Response:
    """Hapus kelas yang diizinkan dan tidak terhalang relasi.

    \f

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        class_id: UUID kelas yang menjadi cakupan operasi.
        db: Session database; batas commit mengikuti operasi terkait.
        current_user: Akun aktif pemanggil sebagai dasar pemeriksaan
            akses.

    Returns:
        Respons HTTP 204 tanpa body.
    """
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
    """Daftarkan mahasiswa pada kelas yang belum terkunci.

    \f

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        class_id: UUID kelas yang menjadi cakupan operasi.
        payload: Data masukan yang sudah melewati validasi schema
            endpoint.
        db: Session database; batas commit mengikuti operasi terkait.
        current_user: Akun aktif pemanggil sebagai dasar pemeriksaan
            akses.

    Returns:
        Keikutsertaan baru beserta profil mahasiswa.
    """
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
    """Sajikan roster kelas yang boleh diakses pengguna.

    \f

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        class_id: UUID kelas yang menjadi cakupan operasi.
        db: Session database; batas commit mengikuti operasi terkait.
        current_user: Akun aktif pemanggil sebagai dasar pemeriksaan
            akses.

    Returns:
        Daftar keikutsertaan dan profil mahasiswa; bisa kosong.
    """
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
    """Hapus keikutsertaan dari roster kelas yang belum terkunci.

    \f

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        class_id: UUID kelas yang menjadi cakupan operasi.
        enrollment_id: UUID keikutsertaan mahasiswa pada satu kelas.
        db: Session database; batas commit mengikuti operasi terkait.
        current_user: Akun aktif pemanggil sebagai dasar pemeriksaan
            akses.

    Returns:
        Respons HTTP 204 tanpa body.
    """
    await class_service.delete_enrollment(db, class_id, enrollment_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
