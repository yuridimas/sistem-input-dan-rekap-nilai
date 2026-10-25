"""Delivery state transitions, durable enqueue failures, and manual retry."""

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.grade import GradeStatus
from app.models.notification import Notification, NotificationStatus
from app.repositories import notifications as repo
from app.services import mailer
from app.services.release_notifications import publish_grade_releases

logger = logging.getLogger(__name__)


async def list_notifications(db: AsyncSession, status: NotificationStatus | None) -> list[Notification]:
    return await repo.list_notifications(db, status)


async def record_enqueue_result(
    db: AsyncSession, grade_ids: list[uuid.UUID], accepted: int, dispatch_tokens: dict[uuid.UUID, uuid.UUID],
) -> None:
    if accepted >= len(grade_ids):
        return
    try:
        await repo.mark_enqueue_failed(db, {grade_id: dispatch_tokens[grade_id] for grade_id in grade_ids[accepted:]})
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("Gagal mencatat kegagalan antrean untuk nilai %s", grade_ids[accepted:])


async def retry_notification(db: AsyncSession, notification_id: uuid.UUID) -> Notification:
    notification = await repo.get_by_id(db, notification_id, lock=True)
    if notification is None:
        raise HTTPException(404, "Notifikasi tidak ditemukan")
    if notification.status == NotificationStatus.SENT:
        raise HTTPException(409, "Notifikasi sudah terkirim")
    details = await repo.delivery_details(db, notification.grade_id)
    if details is None or details[0].status != GradeStatus.FINALIZED:
        raise HTTPException(409, "Nilai belum difinalisasi")
    notification.student_email = details[1].email
    notification.status = NotificationStatus.QUEUED
    notification.error_message = None
    notification.dispatch_token = dispatch_token = uuid.uuid4()
    grade_id = notification.grade_id
    await db.commit()
    accepted = await publish_grade_releases([grade_id])
    await record_enqueue_result(db, [grade_id], accepted, {grade_id: dispatch_token})
    await db.refresh(notification)
    return notification


async def deliver_grade(
    db: AsyncSession, grade_id: uuid.UUID, *, final_attempt: bool, dispatch_token: uuid.UUID | None = None,
) -> dict[str, str]:
    # A grade lock also serializes duplicate legacy messages without a notification row.
    details = await repo.delivery_details(db, grade_id, lock=True)
    if details is None or details[0].status != GradeStatus.FINALIZED:
        await db.rollback()
        return {"status": "ignored"}
    grade, student, course, class_, rank = details
    notification = await repo.get_by_grade(db, grade_id)
    if notification is None and dispatch_token is not None:
        await db.rollback()
        return {"status": "ignored"}
    if notification is None:
        notification = Notification(grade_id=grade_id, student_email=student.email)
        db.add(notification)
        await db.flush()
    if dispatch_token is not None and notification.dispatch_token != dispatch_token:
        await db.commit()
        return {"status": "ignored"}
    if notification.status == NotificationStatus.SENT or grade.release_notified_at is not None:
        notification.status = NotificationStatus.SENT
        notification.sent_at = grade.release_notified_at or notification.sent_at or datetime.now(timezone.utc)
        grade.release_notified_at = notification.sent_at
        notification.error_message = None
        await db.commit()
        return {"status": "already_sent"}
    if notification.status == NotificationStatus.FAILED:
        error = notification.error_message or "Pengiriman gagal; diperlukan pengiriman ulang oleh admin"
        await db.commit()
        return {"status": "failed", "error": error}
    data = mailer.GradeEmail(grade_id, notification.student_email, student.full_name,
                             course.name, class_.section, grade.final_score, rank)
    try:
        # Validate before the mockable SMTP boundary so absent recipients cannot be marked sent.
        mailer.validate_address(data.recipient)
        await asyncio.to_thread(mailer.send_grade_email, data)
    except Exception as exc:
        message = f"{type(exc).__name__}: {exc}"[:2000]
        retry = not final_attempt and not isinstance(exc, ValueError)
        notification.status = NotificationStatus.QUEUED if retry else NotificationStatus.FAILED
        notification.error_message = message
        await db.commit()
        return {"status": "retry" if retry else "failed", "error": message,
                "dispatch_token": str(notification.dispatch_token)}
    sent_at = datetime.now(timezone.utc)
    notification.status = NotificationStatus.SENT
    notification.error_message = None
    notification.sent_at = sent_at
    grade.release_notified_at = sent_at
    await db.commit()
    return {"status": "sent"}
