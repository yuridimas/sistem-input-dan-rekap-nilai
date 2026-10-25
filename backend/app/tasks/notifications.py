"""Grade-release email task with three exponential-backoff retries."""

import asyncio
import uuid

from celery import Task
from celery.exceptions import Retry
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.celery_app import celery_app
from app.config import get_settings
from app.services.notifications import deliver_grade, record_enqueue_result


async def _run(
    grade_id: uuid.UUID, final_attempt: bool, *, publish_failed: bool = False,
    dispatch_token: uuid.UUID | None = None,
) -> dict[str, str]:
    # Each sync Celery invocation has its own event loop; never reuse pooled asyncpg connections.
    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    try:
        async with async_sessionmaker(engine, expire_on_commit=False)() as db:
            if publish_failed:
                if dispatch_token is not None:
                    await record_enqueue_result(db, [grade_id], 0, {grade_id: dispatch_token})
                return {"status": "failed"}
            return await deliver_grade(db, grade_id, final_attempt=final_attempt, dispatch_token=dispatch_token)
    finally:
        await engine.dispose()


@celery_app.task(bind=True, name="app.tasks.notifications.send_grade_release_email", max_retries=3)
def send_grade_release_email(self: Task, grade_id: str, dispatch_token: str | None = None) -> dict[str, str]:
    grade_uuid = uuid.UUID(grade_id)
    token = uuid.UUID(dispatch_token) if dispatch_token else None
    outcome = asyncio.run(_run(grade_uuid, self.request.retries >= self.max_retries, dispatch_token=token))
    if outcome["status"] == "retry":
        try:
            raise self.retry(args=[grade_id], kwargs={"dispatch_token": outcome["dispatch_token"]},
                             exc=RuntimeError(outcome["error"]), countdown=2 ** self.request.retries)
        except Retry:
            raise
        except Exception:
            return asyncio.run(_run(grade_uuid, True, publish_failed=True,
                                     dispatch_token=uuid.UUID(outcome["dispatch_token"])))
    return outcome
