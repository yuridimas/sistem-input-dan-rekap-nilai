"""Superadmin notification audit and recovery endpoints."""

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
    return [NotificationRead.model_validate(row) for row in await service.list_notifications(db, status)]


@router.post("/{notification_id}/retry", response_model=NotificationRead, status_code=202)
async def retry(
    notification_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(_admin),
) -> NotificationRead:
    return NotificationRead.model_validate(await service.retry_notification(db, notification_id))
