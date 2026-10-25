"""Authorized PDF downloads for finalized student/class grades."""

import uuid

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User
from app.services import reports as service

router = APIRouter(prefix="/reports", tags=["reports"])
_roles = require_role("superadmin", "lecturer")
_XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _download(content: bytes, filename: str, media_type: str = "application/pdf") -> Response:
    return Response(content, media_type=media_type, headers={
        "Content-Disposition": f'attachment; filename="{filename}"', "Cache-Control": "no-store",
    })


@router.get("/student/{enrollment_id}/pdf", response_class=Response)
async def student_pdf(
    enrollment_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(_roles),
) -> Response:
    report = await service.load_student_report(db, enrollment_id, user)
    return _download(await service.render_pdf(report, student=True), f"nilai-mahasiswa-{enrollment_id}.pdf")


@router.get("/class/{class_id}/pdf", response_class=Response)
async def class_pdf(
    class_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(_roles),
) -> Response:
    report = await service.load_class_report(db, class_id, user)
    return _download(await service.render_pdf(report, student=False), f"rekap-kelas-{class_id}.pdf")


@router.get("/class/{class_id}/xlsx", response_class=Response)
async def class_xlsx(
    class_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(_roles),
) -> Response:
    report = await service.load_class_report(db, class_id, user)
    return _download(await service.render_xlsx(report), f"rekap-kelas-{class_id}.xlsx", _XLSX_MEDIA_TYPE)
