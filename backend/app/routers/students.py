"""Student management router.

Adapter HTTP profil mahasiswa yang didaftarkan app.main.

Dependency menetapkan identitas/role; aturan bisnis dan persistence
didelegasikan ke service.
"""

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
    """Buat profil mahasiswa untuk pemakaian lintas roster.

    \f

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        payload: Data masukan yang sudah melewati validasi schema
            endpoint.
        db: Session database; batas commit mengikuti operasi terkait.
        current_user: Akun aktif pemanggil sebagai dasar pemeriksaan
            akses.

    Returns:
        Profil mahasiswa baru.
    """
    student = await student_service.create_student(db, payload)
    return StudentRead.model_validate(student)


@router.get("", response_model=list[StudentRead])
async def list_students(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "lecturer")),
) -> list[StudentRead]:
    """Sajikan daftar profil global bagi dosen dan admin.

    \f

    Daftar profil bersifat global; pembatasan kelas diterapkan pada
    roster.

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        current_user: Akun aktif pemanggil sebagai dasar pemeriksaan
            akses.

    Returns:
        Daftar profil mahasiswa global; bisa kosong.
    """
    students = await student_service.list_students(db)
    return [StudentRead.model_validate(student) for student in students]


@router.get("/{student_id}", response_model=StudentRead)
async def get_student(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin", "lecturer")),
) -> StudentRead:
    """Sajikan profil mahasiswa kepada pengguna yang diizinkan.

    \f

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        student_id: UUID profil mahasiswa, bukan UUID enrollment.
        db: Session database; batas commit mengikuti operasi terkait.
        current_user: Akun aktif pemanggil sebagai dasar pemeriksaan
            akses.

    Returns:
        Profil mahasiswa yang diminta.
    """
    student = await student_service.get_student(db, student_id)
    return StudentRead.model_validate(student)


@router.patch("/{student_id}", response_model=StudentRead)
async def update_student(
    student_id: uuid.UUID,
    payload: StudentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin")),
) -> StudentRead:
    """Ubah profil global mahasiswa melalui superadmin.

    \f

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        student_id: UUID profil mahasiswa, bukan UUID enrollment.
        payload: Data masukan yang sudah melewati validasi schema
            endpoint.
        db: Session database; batas commit mengikuti operasi terkait.
        current_user: Akun aktif pemanggil sebagai dasar pemeriksaan
            akses.

    Returns:
        Profil mahasiswa terbaru.
    """
    student = await student_service.update_student(db, student_id, payload)
    return StudentRead.model_validate(student)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("superadmin")),
) -> Response:
    """Hapus profil mahasiswa melalui superadmin.

    \f

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        student_id: UUID profil mahasiswa, bukan UUID enrollment.
        db: Session database; batas commit mengikuti operasi terkait.
        current_user: Akun aktif pemanggil sebagai dasar pemeriksaan
            akses.

    Returns:
        Respons HTTP 204 tanpa body.
    """
    await student_service.delete_student(db, student_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
