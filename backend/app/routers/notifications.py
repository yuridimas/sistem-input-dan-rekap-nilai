"""Superadmin notification audit and recovery endpoints.

Adapter HTTP audit dan retry notifikasi yang didaftarkan app.main.

Dependency menetapkan identitas/role; aturan bisnis dan persistence
didelegasikan ke service.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.notification import NotificationStatus
from app.models.user import User
from app.schemas.notifications import NotificationRead
from app.services import notifications as service

router = APIRouter(prefix="/admin/notifications", tags=["notifications"])
_admin = require_role("superadmin")


@router.get("", response_model=list[NotificationRead])
async def list_notifications(
    status: NotificationStatus | None = None, db: AsyncSession = Depends(get_db), user: User = Depends(_admin),
) -> list[NotificationRead]:
    """Sajikan audit pengiriman terfilter untuk superadmin.

    \f

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        status: Filter status pengiriman; None menyertakan seluruh
            status.
        db: Session database; batas commit mengikuti operasi terkait.
        user: Objek akun untuk pemeriksaan akses atau persistence sesuai
            operasi.

    Returns:
        Daftar catatan pengiriman sesuai filter; bisa kosong.
    """
    return [NotificationRead.model_validate(row) for row in await service.list_notifications(db, status)]


@router.post("/{notification_id}/retry", response_model=NotificationRead, status_code=202)
async def retry(
    notification_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(_admin),
) -> NotificationRead:
    """Siapkan percobaan pengiriman baru untuk notifikasi.

    \f

    Respons 202 menyatakan percobaan baru disiapkan, bukan delivery
    berhasil.

    Error akses/validasi/konflik diteruskan dari dependency/service.

    Args:
        notification_id: UUID catatan pengiriman yang dibaca atau
            dipulihkan.
        db: Session database; batas commit mengikuti operasi terkait.
        user: Objek akun untuk pemeriksaan akses atau persistence sesuai
            operasi.

    Returns:
        Catatan pengiriman terbaru setelah percobaan enqueue.
    """
    return NotificationRead.model_validate(await service.retry_notification(db, notification_id))
