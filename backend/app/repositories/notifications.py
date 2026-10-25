"""Notification persistence; calling services own transactions."""

import uuid

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.class_ import Class
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.grade import Grade
from app.models.notification import Notification, NotificationStatus
from app.models.ranking import Ranking
from app.models.student import Student


def add_releases(db: AsyncSession, releases: list[tuple[uuid.UUID, str | None]]) -> dict[uuid.UUID, uuid.UUID]:
    rows = [Notification(grade_id=grade_id, student_email=email, dispatch_token=uuid.uuid4()) for grade_id, email in releases]
    db.add_all(rows)
    return {row.grade_id: row.dispatch_token for row in rows}


async def get_by_id(db: AsyncSession, notification_id: uuid.UUID, *, lock: bool = False) -> Notification | None:
    stmt = select(Notification).where(Notification.id == notification_id).execution_options(populate_existing=True)
    if lock:
        stmt = stmt.with_for_update()
    return (await db.execute(stmt)).scalar_one_or_none()


async def get_by_grade(db: AsyncSession, grade_id: uuid.UUID) -> Notification | None:
    return (await db.execute(select(Notification).where(Notification.grade_id == grade_id)
                             .with_for_update().execution_options(populate_existing=True))).scalar_one_or_none()


async def list_notifications(db: AsyncSession, status: NotificationStatus | None) -> list[Notification]:
    stmt = select(Notification).order_by(Notification.created_at.desc(), Notification.id)
    if status is not None:
        stmt = stmt.where(Notification.status == status)
    return list((await db.execute(stmt)).scalars())


async def delivery_details(
    db: AsyncSession, grade_id: uuid.UUID, *, lock: bool = False,
) -> tuple[Grade, Student, Course, Class, int | None] | None:
    stmt = (select(Grade, Student, Course, Class, Ranking.rank).select_from(Grade)
            .join(Enrollment, Enrollment.id == Grade.enrollment_id)
            .join(Student, Student.id == Enrollment.student_id)
            .join(Class, Class.id == Enrollment.class_id)
            .join(Course, Course.id == Class.course_id)
            .outerjoin(Ranking, and_(Ranking.enrollment_id == Enrollment.id, Ranking.class_id == Class.id))
            .where(Grade.id == grade_id).execution_options(populate_existing=True))
    if lock:
        stmt = stmt.with_for_update(of=Grade)
    return (await db.execute(stmt)).one_or_none()


async def mark_enqueue_failed(db: AsyncSession, dispatch_tokens: dict[uuid.UUID, uuid.UUID]) -> None:
    if dispatch_tokens:
        await db.execute(update(Notification).where(
            or_(*(and_(Notification.grade_id == grade_id, Notification.dispatch_token == token)
                  for grade_id, token in dispatch_tokens.items())),
            Notification.status == NotificationStatus.QUEUED,
        ).values(status=NotificationStatus.FAILED, error_message="Antrean tidak tersedia; kirim ulang notifikasi"))
