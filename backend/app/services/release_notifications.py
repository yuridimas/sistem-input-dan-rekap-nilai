"""Best-effort queue publishing after grades have committed."""

import asyncio
import logging
import uuid

from app.celery_app import celery_app

logger = logging.getLogger(__name__)
GRADE_RELEASE_TASK = "app.tasks.notifications.send_grade_release_email"


async def publish_grade_releases(grade_ids: list[uuid.UUID]) -> int:
    published = 0
    for grade_id in grade_ids:
        try:
            await asyncio.to_thread(
                celery_app.send_task, GRADE_RELEASE_TASK, args=[str(grade_id)], retry=False,
            )
        except Exception:
            logger.exception("Gagal mengantrekan notifikasi; ID nilai belum terantre: %s", grade_ids[published:])
            break
        published += 1
    return published
