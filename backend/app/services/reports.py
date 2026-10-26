"""Final-only report loading and offloaded PDF/XLSX rendering.

Pemuatan data final dan rendering laporan untuk router reports.

Objek ReportData dipisahkan dari ORM agar renderer PDF/XLSX dapat
bekerja di thread.
"""

import asyncio
import io
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
    """Tolak data draft sebelum dibentuk sebagai baris laporan resmi.

    Args:
        row: Hasil query enrollment, mahasiswa, nilai opsional, dan
            ranking.

    Raises:
        HTTPException: 409 jika Grade kosong atau belum finalized.
    """
    enrollment, student, grade, rank = row
    if grade is None or grade.status != GradeStatus.FINALIZED:
        raise HTTPException(409, "PDF hanya tersedia untuk nilai yang sudah difinalisasi")
    return ReportRow(enrollment_id=enrollment.id, nim=student.nim, full_name=student.full_name,
                     final_score=grade.final_score, rank=rank, finalized_at=grade.finalized_at)


async def _report_context(db: AsyncSession, class_: Class, rows: list[ReportRow]) -> ReportData:
    """Lengkapi metadata mata kuliah/kelas untuk kedua jenis laporan.

    Hanya membaca DB.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        class_: Objek kelas yang sudah dimuat oleh pemanggil.
        rows: Data sumber yang sudah dimuat untuk perakitan atau audit.

    Raises:
        HTTPException: 404 jika mata kuliah absen.
    """
    course = await course_repo.get_by_id(db, class_.course_id)
    if course is None:
        raise HTTPException(404, "Mata kuliah tidak ditemukan")
    return ReportData(class_id=class_.id, course_name=course.name, course_code=course.code,
                      semester=course.semester, section=class_.section,
                      academic_year=class_.academic_year, rows=rows)


async def load_student_report(db: AsyncSession, enrollment_id: uuid.UUID, user: User) -> ReportData:
    """Muat nilai final satu enrollment setelah pemeriksaan akses kelas.

    Hanya membaca DB.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        enrollment_id: UUID keikutsertaan mahasiswa pada satu kelas.
        user: Objek akun untuk pemeriksaan akses atau persistence sesuai
            operasi.

    Raises:
        HTTPException: 403/404 akses atau 409 belum final.
    """
    row = await repo.get_student(db, enrollment_id)
    if row is None:
        raise HTTPException(404, "Pendaftaran mahasiswa tidak ditemukan")
    class_ = await get_class(db, row[0].class_id, user)
    report = await _report_context(db, class_, [_report_row(row)])
    component_rows = await history_repo.list_components(db, [enrollment_id])
    report.components = [ReportComponent(id=component.id, name=component.name, category=component.category,
                                         weight=component.weight, max_score=component.max_score, score=score)
                         for _id, component, score in component_rows]
    report.component_scores = {enrollment_id: {component.id: score for _, component, score in component_rows}}
    return report


async def load_class_report(db: AsyncSession, class_id: uuid.UUID, user: User) -> ReportData:
    """Muat roster final beserta peta skor untuk laporan seluruh kelas.

    Hanya membaca DB.

    Args:
        db: Session database; batas commit mengikuti operasi terkait.
        class_id: UUID kelas yang menjadi cakupan operasi.
        user: Objek akun untuk pemeriksaan akses atau persistence sesuai
            operasi.

    Raises:
        HTTPException: 403/404 akses atau 409 kosong/belum final.
    """
    class_ = await get_class(db, class_id, user)
    rows = await repo.list_class(db, class_id)
    if not rows:
        raise HTTPException(409, "Kelas belum memiliki nilai final untuk diekspor")
    report = await _report_context(db, class_, [_report_row(row) for row in rows])
    component_rows = await history_repo.list_components(db, [row.enrollment_id for row in report.rows])
    component_by_id: dict[uuid.UUID, ReportComponent] = {}
    for enrollment_id, component, score in component_rows:
        component_by_id.setdefault(component.id, ReportComponent(
            id=component.id, name=component.name, category=component.category,
            weight=component.weight, max_score=component.max_score, score=None,
        ))
        report.component_scores.setdefault(enrollment_id, {})[component.id] = score
    report.components = list(component_by_id.values())
    return report


def reject_resource(url: str, *args: Any, **kwargs: Any) -> NoReturn:
    """Tolak seluruh akses resource eksternal renderer PDF.

    Args:
        url: Resource yang diminta renderer; seluruh akses ditolak.
        *args: Argumen tambahan sesuai kontrak callback pemanggil.
        **kwargs: Keyword tambahan sesuai kontrak callback pemanggil.

    Raises:
        ValueError: Setiap permintaan resource ditolak.
    """
    raise ValueError("Resource eksternal tidak diizinkan dalam laporan PDF")


def _load_weasyprint() -> Any:
    """Tunda import renderer agar route lain tetap tersedia.

    ImportError/OSError diterjemahkan pemanggil menjadi HTTPException
    503.

    Returns:
        Class HTML dari WeasyPrint untuk membuat dokumen PDF.
    """
    from weasyprint import HTML
    return HTML


def _decimal(value: Decimal | None) -> str:
    """Format dua desimal berkoma atau penanda kosong untuk None.

    Tanpa mutasi atau akses eksternal.

    Args:
        value: Decimal opsional; None memakai penanda kosong.

    Returns:
        Teks dua desimal berkoma, atau penanda kosong jika value None.
    """
    return "—" if value is None else format(value, ".2f").replace(".", ",")


def _render_pdf(template_name: str, report: ReportData, institution_name: str) -> bytes:
    """Render PDF dalam memori tanpa resource eksternal.

    Error template/render lain diteruskan.

    Args:
        template_name: Nama template lokal yang dipilih service, bukan
            path bebas.
        report: Konteks laporan yang sudah lolos validasi akses dan
            status final.
        institution_name: Nama institusi dari konfigurasi untuk header
            laporan.

    Raises:
        HTTPException: 503 jika runtime absen.

    Returns:
        Bytes dokumen PDF yang sudah dirender.
    """
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
    """Offload renderer PDF sinkron ke thread.

    Exception renderer diteruskan.

    Args:
        report: Konteks laporan yang sudah lolos validasi akses dan
            status final.
        student: True memilih laporan individu; False memilih rekap
            kelas.

    Returns:
        Bytes dokumen PDF dari template individu atau kelas.
    """
    return await asyncio.to_thread(_render_pdf, "student_report.html" if student else "class_report.html",
                                   report, get_settings().institution_name)


def _render_xlsx(report: ReportData) -> bytes:
    """Bangun workbook dalam memori tanpa file sementara.

    Exception workbook diteruskan.

    Args:
        report: Konteks laporan yang sudah lolos validasi akses dan
            status final.

    Raises:
        HTTPException: 503 jika openpyxl absen.

    Returns:
        Bytes workbook XLSX yang dibangun dalam memori.
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill
    except ImportError as exc:
        raise HTTPException(503, "Export Excel belum tersedia; periksa dependensi workbook") from exc

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Rekap Kelas"

    def text_cell(cell: Any, value: str) -> None:
        """Paksa teks agar NIM utuh dan formula tidak dieksekusi."""
        cell.value = value
        cell.data_type = "s"

    headers = ["NIM", "Nama"]
    headers.extend(
        f"{component.name} ({component.category}, bobot {_decimal(component.weight)}%, maks {_decimal(component.max_score)})"
        for component in report.components
    )
    headers.extend(["Nilai Akhir", "Peringkat", "Status"])
    for column, value in enumerate(headers, start=1):
        text_cell(sheet.cell(row=1, column=column), value)
        sheet.cell(row=1, column=column).font = Font(bold=True, color="FFFFFF")
        sheet.cell(row=1, column=column).fill = PatternFill(fill_type="solid", fgColor="1F4E78")
        sheet.cell(row=1, column=column).alignment = Alignment(wrap_text=True, vertical="center")

    for row_index, report_row in enumerate(report.rows, start=2):
        text_cell(sheet.cell(row=row_index, column=1), report_row.nim)
        text_cell(sheet.cell(row=row_index, column=2), report_row.full_name)
        scores = report.component_scores.get(report_row.enrollment_id, {})
        for column, component in enumerate(report.components, start=3):
            cell = sheet.cell(row=row_index, column=column, value=scores.get(component.id))
            cell.number_format = "0.00"
        final_column = len(report.components) + 3
        sheet.cell(row=row_index, column=final_column, value=report_row.final_score).number_format = "0.00"
        sheet.cell(row=row_index, column=final_column + 1, value=report_row.rank)
        text_cell(sheet.cell(row=row_index, column=final_column + 2),
                  "Tidak lulus" if report_row.final_score < 45 else "Lulus")

    # Header tetap terlihat; lebar 12..55 membatasi kolom agar label panjang tidak mendominasi.
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    sheet.row_dimensions[1].height = 32
    for column in sheet.columns:
        letter = column[0].column_letter
        width = max(len(str(cell.value or "")) for cell in column) + 2
        sheet.column_dimensions[letter].width = min(max(width, 12), 55)

    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()


async def render_xlsx(report: ReportData) -> bytes:
    """Offload pembuatan workbook sinkron ke thread.

    Exception renderer diteruskan.

    Args:
        report: Konteks laporan yang sudah lolos validasi akses dan
            status final.

    Returns:
        Bytes workbook XLSX yang siap dikirim sebagai unduhan.
    """
    return await asyncio.to_thread(_render_xlsx, report)
