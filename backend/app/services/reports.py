"""Final-only report loading and thread-isolated WeasyPrint rendering."""

import asyncio
import logging
import uuid
from datetime import timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, NoReturn

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.class_ import Class
from app.models.enrollment import Enrollment
from app.models.grade import Grade, GradeStatus
from app.models.student import Student
from app.models.user import User
from app.repositories import course as course_repo
from app.repositories import history as history_repo
from app.repositories import reports as repo
from app.schemas.reports import ReportComponent, ReportData, ReportRow
from app.services.class_ import get_class

logger = logging.getLogger(__name__)


def _report_row(row: tuple[Enrollment, Student, Grade | None, int | None]) -> ReportRow:
    enrollment, student, grade, rank = row
    if grade is None or grade.status != GradeStatus.FINALIZED:
        raise HTTPException(409, "PDF hanya tersedia untuk nilai yang sudah difinalisasi")
    return ReportRow(enrollment_id=enrollment.id, nim=student.nim, full_name=student.full_name,
                     final_score=grade.final_score, rank=rank, finalized_at=grade.finalized_at)


async def _report_context(db: AsyncSession, class_: Class, rows: list[ReportRow]) -> ReportData:
    course = await course_repo.get_by_id(db, class_.course_id)
    if course is None:
        raise HTTPException(404, "Mata kuliah tidak ditemukan")
    return ReportData(class_id=class_.id, course_name=course.name, course_code=course.code,
                      semester=course.semester, section=class_.section,
                      academic_year=class_.academic_year, rows=rows)


async def load_student_report(db: AsyncSession, enrollment_id: uuid.UUID, user: User) -> ReportData:
    row = await repo.get_student(db, enrollment_id)
    if row is None:
        raise HTTPException(404, "Pendaftaran mahasiswa tidak ditemukan")
    class_ = await get_class(db, row[0].class_id, user)
    report = await _report_context(db, class_, [_report_row(row)])
    report.components = [ReportComponent(name=component.name, category=component.category,
                                         weight=component.weight, max_score=component.max_score, score=score)
                         for _id, component, score in await history_repo.list_components(db, [enrollment_id])]
    return report


async def load_class_report(db: AsyncSession, class_id: uuid.UUID, user: User) -> ReportData:
    class_ = await get_class(db, class_id, user)
    rows = await repo.list_class(db, class_id)
    if not rows:
        raise HTTPException(409, "Kelas belum memiliki nilai final untuk diekspor")
    return await _report_context(db, class_, [_report_row(row) for row in rows])


def reject_resource(url: str, *args: Any, **kwargs: Any) -> NoReturn:
    raise ValueError("Resource eksternal tidak diizinkan dalam laporan PDF")


def _load_weasyprint() -> Any:
    from weasyprint import HTML
    return HTML


def _decimal(value: Decimal | None) -> str:
    return "—" if value is None else format(value, ".2f").replace(".", ",")


def _render_pdf(template_name: str, report: ReportData, institution_name: str) -> bytes:
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
        html_class = _load_weasyprint()
    except (ImportError, OSError) as exc:
        logger.error("Runtime PDF belum tersedia: %s", type(exc).__name__)
        raise HTTPException(503, "Export PDF belum tersedia; periksa dependensi renderer") from exc
    templates = Path(__file__).resolve().parent.parent / "templates"
    environment = Environment(loader=FileSystemLoader(templates), autoescape=select_autoescape(["html"]))
    environment.filters["decimal"] = _decimal
    environment.filters["released_at"] = lambda value: value.astimezone(timezone.utc).strftime("%d/%m/%Y %H:%M UTC") if value else "—"
    html = environment.get_template(template_name).render(report=report, institution_name=institution_name)
    return html_class(string=html, url_fetcher=reject_resource).write_pdf()


async def render_pdf(report: ReportData, *, student: bool) -> bytes:
    return await asyncio.to_thread(_render_pdf, "student_report.html" if student else "class_report.html",
                                   report, get_settings().institution_name)
