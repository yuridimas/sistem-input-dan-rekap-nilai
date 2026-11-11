"""Query agregasi dashboard sebelum join mata kuliah dan kelas.

Batched dashboard reads; aggregate before joining courses and classes.

Query dan persistence agregasi dashboard bagi service terkait.

Commit/rollback dimiliki service; error database diteruskan kecuali
disebutkan.
"""

import uuid

from sqlalchemy import RowMapping, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.class_ import Class
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.grade import Grade, GradeStatus
from app.models.score import Score


async def list_summary_rows(db: AsyncSession, lecturer_id: uuid.UUID | None) -> list[RowMapping]:
    """Agregasikan roster/nilai sebelum join dashboard.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        lecturer_id: UUID dosen penugasan; None membuka ringkasan
            superadmin.

    Returns:
        Baris agregat per mata kuliah/kelas; kelas kosong tetap
        terwakili melalui outer join.
    """
    counts = (
        select(
            Enrollment.class_id,
            func.count(Enrollment.id).label("student_count"),
            func.count(case((Grade.status == GradeStatus.FINALIZED, 1))).label("finalized_count"),
            func.max(case((Grade.status == GradeStatus.FINALIZED, Grade.finalized_at))).label("released_at"),
        )
        .outerjoin(Grade, Grade.enrollment_id == Enrollment.id)
        .group_by(Enrollment.class_id)
        .subquery()
    )
    activity = (
        select(
            Enrollment.class_id,
            func.max(Enrollment.enrolled_at).label("enrollment_updated_at"),
            func.max(Score.updated_at).label("score_updated_at"),
            func.max(Grade.finalized_at).label("grade_updated_at"),
        )
        .outerjoin(Score, Score.enrollment_id == Enrollment.id)
        .outerjoin(Grade, Grade.enrollment_id == Enrollment.id)
        .group_by(Enrollment.class_id)
        .subquery()
    )
    statement = (
        select(
            Course.id.label("course_id"), Course.code, Course.name, Course.semester, Course.created_at,
            Class.id.label("class_id"), Class.section, Class.academic_year,
            func.coalesce(counts.c.student_count, 0).label("student_count"),
            func.coalesce(counts.c.finalized_count, 0).label("finalized_count"),
            counts.c.released_at,
            func.greatest(Class.created_at, activity.c.enrollment_updated_at, activity.c.score_updated_at, activity.c.grade_updated_at).label("updated_at"),
        )
        .select_from(Course)
        .outerjoin(Class, Class.course_id == Course.id)
        .outerjoin(counts, counts.c.class_id == Class.id)
        .outerjoin(activity, activity.c.class_id == Class.id)
        .order_by(Course.created_at.desc(), Course.id, Class.academic_year.desc(), Class.section, Class.id)
    )
    if lecturer_id is not None:
        statement = statement.where(Class.lecturer_id == lecturer_id)
    return list((await db.execute(statement)).mappings().all())
