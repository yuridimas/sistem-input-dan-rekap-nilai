"""Assemble scoped course/class summaries without modifying grades."""

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.repositories import dashboard as dashboard_repo
from app.schemas.dashboard import (
    DashboardClassRead, DashboardCourseRead, DashboardReleaseRead, DashboardSummaryRead,
)


async def get_summary(db: AsyncSession, current_user: User) -> DashboardSummaryRead:
    lecturer_id = None if current_user.role == UserRole.SUPERADMIN.value else current_user.id
    rows = await dashboard_repo.list_summary_rows(db, lecturer_id)
    courses = {}
    releases = []
    class_count = pending_count = 0
    for row in rows:
        course_id = row["course_id"]
        if course_id not in courses:
            courses[course_id] = DashboardCourseRead(
                id=course_id, code=row["code"], name=row["name"], semester=row["semester"], classes=[],
            )
        if row["class_id"] is None:
            continue
        released = row["student_count"] > 0 and row["finalized_count"] == row["student_count"]
        class_ = DashboardClassRead(
            id=row["class_id"], section=row["section"], academic_year=row["academic_year"],
            student_count=row["student_count"], status="released" if released else "pending",
            released_at=row["released_at"] if released else None,
        )
        courses[course_id].classes.append(class_)
        class_count += 1
        pending_count += int(not released)
        if released:
            releases.append(DashboardReleaseRead(
                **class_.model_dump(), course_id=course_id,
                course_code=row["code"], course_name=row["name"],
            ))
    releases.sort(key=lambda item: str(item.id))
    releases.sort(key=lambda item: item.released_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return DashboardSummaryRead(
        course_count=len(courses), class_count=class_count, pending_class_count=pending_count,
        courses=list(courses.values()), recently_released=releases[:5],
    )
