"""Uji export PDF/XLSX final dan batas akses laporan.

Final-only PDF downloads, access boundaries, and real rendered content.

Export final, keamanan rendering, dan integritas unduhan.

Memerlukan PostgreSQL disposable yang dimigrasi; beberapa skenario
melakukan commit nyata.
"""

import io
import threading
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import delete, event, select, update

from app.database import engine
from app.models.enrollment import Enrollment
from app.models.grade import Grade
from app.models.ranking import Ranking
from app.models.score import Score
from app.models.student import Student
from app.models.user import User
from app.services.auth import decode_token
from tests.test_finalization import fill_scores, mock_publisher
from tests.test_scores import grading_context


def pdf_text(response):
    """Validasi unduhan PDF lalu ekstrak teks untuk assertion."""
    from pypdf import PdfReader

    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["cache-control"] == "no-store"
    assert response.content.startswith(b"%PDF-")
    return "\n".join(page.extract_text() for page in PdfReader(io.BytesIO(response.content)).pages)


async def finalize(context, monkeypatch):
    """Siapkan rilis resmi melalui API dan publisher palsu."""
    client, class_id, _enrollments, _components, (owner, _, _), _db = context
    mock_publisher(monkeypatch)
    await fill_scores(context)
    response = await client.post(f"/classes/{class_id}/finalize", headers=owner)
    assert response.status_code == 202, response.text


@pytest.mark.asyncio
async def test_student_pdf_has_component_details_and_attachment(grading_context, monkeypatch):
    """Sertakan rincian resmi dalam attachment PDF individu."""
    client, _class_id, enrollments, components, (owner, _, _), db = grading_context
    await finalize(grading_context, monkeypatch)
    enrollment = await db.get(Enrollment, uuid.UUID(enrollments[0]))
    student = await db.get(Student, enrollment.student_id)
    response = await client.get(f"/reports/student/{enrollments[0]}/pdf", headers=owner)
    text = pdf_text(response)
    assert response.headers["content-disposition"] == f'attachment; filename="nilai-mahasiswa-{enrollments[0]}.pdf"'
    for value in (student.full_name, student.nim, "Penilaian", "2026/1", "2026/2027", "81,00", "Lulus", "Peringkat", "Laporan Nilai Mahasiswa"):
        assert value in text
    assert all(component["name"] in text for component in components), repr(text)
    assert all(value in text for value in ("80,00", "70,00", "90,00", "30,00%", "40,00%", "100,00"))


@pytest.mark.asyncio
async def test_class_pdf_is_summary_and_institution_name_is_configurable(grading_context, monkeypatch):
    """Jaga rekap ringkas dan nama institusi dari konfigurasi."""
    from app.config import Settings

    client, class_id, _enrollments, _components, (_, _, admin), _db = grading_context
    await finalize(grading_context, monkeypatch)
    monkeypatch.setattr("app.services.reports.get_settings", lambda: Settings(_env_file=None, institution_name="Institut Contoh"))
    response = await client.get(f"/reports/class/{class_id}/pdf", headers=admin)
    text = pdf_text(response)
    assert response.headers["content-disposition"] == f'attachment; filename="rekap-kelas-{class_id}.pdf"'
    for value in ("Institut Contoh", "Rekap Nilai Kelas", "Mahasiswa 0", "Mahasiswa 1", "81,00", "Lulus"):
        assert value in text
    assert "Bobot" not in text and "Nilai Maksimum" not in text
    assert text.index("Mahasiswa 0") < text.index("Mahasiswa 1")


@pytest.mark.asyncio
async def test_class_xlsx_contains_finalized_roster_components_and_safe_text(grading_context, monkeypatch):
    """Pertahankan teks aman dan rincian final dalam XLSX."""
    client, class_id, enrollments, components, (owner, _, _), db = grading_context
    await finalize(grading_context, monkeypatch)
    student_id = await db.scalar(select(Enrollment.student_id).where(Enrollment.id == uuid.UUID(enrollments[0])))
    await db.execute(update(Student).where(Student.id == student_id).values(full_name="=1+1"))
    await db.execute(delete(Ranking).where(Ranking.enrollment_id == uuid.UUID(enrollments[0])))
    await db.execute(update(Score).where(Score.enrollment_id == uuid.UUID(enrollments[0]),
                                         Score.component_id == uuid.UUID(components[0]["id"])).values(score=0))
    await db.execute(update(Grade).where(Grade.enrollment_id == uuid.UUID(enrollments[1])).values(final_score=Decimal("44.99")))
    await db.commit()

    response = await client.get(f"/reports/class/{class_id}/xlsx", headers=owner)

    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["content-disposition"] == f'attachment; filename="rekap-kelas-{class_id}.xlsx"'
    from openpyxl import load_workbook

    workbook = load_workbook(io.BytesIO(response.content), data_only=False)
    sheet = workbook["Rekap Kelas"]
    headers = [cell.value for cell in sheet[1]]
    assert headers[:2] == ["NIM", "Nama"]
    assert headers[-3:] == ["Nilai Akhir", "Peringkat", "Status"]
    assert len(headers) == len(components) + 5
    assert sheet.max_row == len(enrollments) + 1
    assert sheet.freeze_panes == "A2" and sheet.auto_filter.ref == sheet.dimensions
    assert sheet[1][0].font.bold and sheet[1][0].fill.fgColor.rgb.endswith("1F4E78")
    assert sheet[2][1].value == "=1+1" and sheet[2][1].data_type != "f"
    assert sheet[2][-3].value == 81 and sheet[2][-2].value is None and sheet[2][-1].value == "Lulus"
    assert sheet[3][-3].value == pytest.approx(44.99) and sheet[3][-1].value == "Tidak lulus"
    assert all(component["name"] in headers[index + 2] for index, component in enumerate(components))
    assert "bobot 30,00%" in headers[2] and "maks 100,00" in headers[2]
    assert [sheet.cell(row=2, column=index + 3).value for index in range(len(components))] == [0, 70, 90]


@pytest.mark.asyncio
async def test_class_xlsx_is_readonly_batched_and_offloaded(grading_context, monkeypatch):
    """Uji query batch, offload, dan export XLSX read-only."""
    from app.services import reports

    client, class_id, _ids, _components, (owner, _, _), db = grading_context
    await finalize(grading_context, monkeypatch)
    calls, commits = [], []
    main_thread = threading.get_ident()
    original = reports._render_xlsx

    def render(report):
        """Kendalikan hasil renderer dan amati thread pemanggil."""
        assert threading.get_ident() != main_thread
        return original(report)

    def record(_conn, _cursor, statement, _params, _context, _many):
        """Catat statement untuk uji anggaran query."""
        calls.append(statement)

    def committed(_session):
        """Amati commit untuk membuktikan export read-only."""
        commits.append(True)

    monkeypatch.setattr(reports, "_render_xlsx", render)
    event.listen(engine.sync_engine, "before_cursor_execute", record)
    event.listen(db.sync_session, "after_commit", committed)
    try:
        response = await client.get(f"/reports/class/{class_id}/xlsx", headers=owner)
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", record)
        event.remove(db.sync_session, "after_commit", committed)
    assert response.status_code == 200, response.text
    queries = [call for call in calls if not call.lstrip().upper().startswith("SAVEPOINT ")]
    assert len(queries) <= 5 and all(call.lstrip().upper().startswith("SELECT") for call in queries)
    assert commits == []


@pytest.mark.asyncio
async def test_class_xlsx_rejects_empty_and_partially_finalized_classes(grading_context):
    """Tolak XLSX untuk roster kosong atau belum final."""
    client, class_id, enrollments, _components, (owner, _, _), db = grading_context
    url = f"/reports/class/{class_id}/xlsx"
    assert (await client.get(url, headers=owner)).status_code == 409
    db.add(Grade(enrollment_id=uuid.UUID(enrollments[0]), final_score=50, status="finalized"))
    await db.commit()
    assert (await client.get(url, headers=owner)).status_code == 409
    await db.execute(delete(Grade).where(Grade.enrollment_id == uuid.UUID(enrollments[0])))
    await db.execute(delete(Enrollment).where(Enrollment.class_id == uuid.UUID(class_id)))
    await db.commit()
    assert (await client.get(url, headers=owner)).status_code == 409


@pytest.mark.asyncio
async def test_pdf_authorization_and_finalized_only(grading_context, monkeypatch):
    """PDF hanya tersedia setelah finalisasi dan pemeriksaan hak baca.
    """
    client, class_id, enrollments, _components, (owner, other, admin), _db = grading_context
    urls = (f"/reports/student/{enrollments[0]}/pdf", f"/reports/class/{class_id}/pdf",
            f"/reports/class/{class_id}/xlsx")
    for url in urls:
        assert (await client.get(url)).status_code == 401
        assert (await client.get(url, headers=other)).status_code == 403
        assert (await client.get(url, headers=owner)).status_code == 409
    for kind in ("student", "class"):
        assert (await client.get(f"/reports/{kind}/{uuid.uuid4()}/pdf", headers=owner)).status_code == 404
        assert (await client.get(f"/reports/{kind}/invalid/pdf", headers=owner)).status_code == 422
    assert (await client.get(f"/reports/class/{uuid.uuid4()}/xlsx", headers=owner)).status_code == 404
    assert (await client.get(f"/reports/class/invalid/xlsx", headers=owner)).status_code == 422
    await fill_scores(grading_context)
    for url in urls:
        assert (await client.get(url, headers=owner)).status_code == 409
    await finalize(grading_context, monkeypatch)
    for url in urls:
        assert (await client.get(url, headers=admin)).status_code == 200


@pytest.mark.asyncio
async def test_pdf_zero_boundary_legacy_rank_and_html_are_preserved(grading_context, monkeypatch):
    """Render nol, batas lulus, rank kosong, dan HTML aman."""
    client, class_id, enrollments, _components, (owner, _, _), db = grading_context
    await finalize(grading_context, monkeypatch)
    student_id = await db.scalar(select(Enrollment.student_id).where(Enrollment.id == uuid.UUID(enrollments[0])))
    await db.execute(update(Student).where(Student.id == student_id).values(full_name="Éka <b>Putri</b> & Nūr"))
    await db.execute(delete(Ranking).where(Ranking.enrollment_id == uuid.UUID(enrollments[0])))
    await db.execute(update(Grade).where(Grade.enrollment_id == uuid.UUID(enrollments[0])).values(final_score=Decimal("44.99"), finalized_at=None))
    await db.commit()
    text = pdf_text(await client.get(f"/reports/student/{enrollments[0]}/pdf", headers=owner))
    assert "Éka <b>Putri</b> & Nūr" in text and "44,99" in text and "Tidak lulus" in text
    assert "Peringkat kelas: —" in text and "Difinalisasi: —" in text
    await db.execute(update(Grade).where(Grade.enrollment_id == uuid.UUID(enrollments[0])).values(final_score=Decimal("45")))
    await db.commit()
    text = pdf_text(await client.get(f"/reports/student/{enrollments[0]}/pdf", headers=owner))
    assert "45,00" in text and "Lulus" in text and "Tidak lulus" not in text
    await db.execute(update(Grade).where(Grade.enrollment_id == uuid.UUID(enrollments[0])).values(final_score=Decimal("0")))
    await db.commit()
    assert "0,00" in pdf_text(await client.get(f"/reports/class/{class_id}/pdf", headers=owner))


@pytest.mark.asyncio
async def test_empty_or_partially_finalized_class_is_not_exportable(grading_context):
    """Tolak export jika roster kosong atau masih draft."""
    client, class_id, enrollments, _components, (owner, _, _), db = grading_context
    db.add(Grade(enrollment_id=uuid.UUID(enrollments[0]), final_score=50, status="finalized"))
    await db.commit()
    assert (await client.get(f"/reports/class/{class_id}/pdf", headers=owner)).status_code == 409
    await db.execute(delete(Grade).where(Grade.enrollment_id == uuid.UUID(enrollments[0])))
    await db.execute(delete(Enrollment).where(Enrollment.class_id == uuid.UUID(class_id)))
    await db.commit()
    assert (await client.get(f"/reports/class/{class_id}/pdf", headers=owner)).status_code == 409


@pytest.mark.asyncio
async def test_unavailable_renderer_returns_503_without_breaking_other_routes(grading_context, monkeypatch):
    """Runtime PDF absen memberi 503 tanpa mematikan route lainnya."""
    from app.services import reports

    client, class_id, _ids, _components, (owner, _, _), _db = grading_context
    await finalize(grading_context, monkeypatch)

    def missing():
        """Simulasikan renderer absen tanpa uninstall package."""
        raise OSError("Pango missing")

    monkeypatch.setattr(reports, "_load_weasyprint", missing)
    response = await client.get(f"/reports/class/{class_id}/pdf", headers=owner)
    assert response.status_code == 503 and "PDF" in response.json()["detail"]
    assert (await client.get(f"/classes/{class_id}/grades", headers=owner)).status_code == 200


@pytest.mark.asyncio
async def test_render_offload_query_budget_and_readonly_export(grading_context, monkeypatch):
    """Uji offload dan query export PDF yang read-only."""
    from app.services import reports

    client, class_id, _ids, _components, (owner, _, _), db = grading_context
    await finalize(grading_context, monkeypatch)
    calls = []
    commits = []
    main_thread = threading.get_ident()
    original = reports._render_pdf

    def render(*args, **kwargs):
        """Kendalikan hasil renderer dan amati thread pemanggil."""
        assert threading.get_ident() != main_thread
        return original(*args, **kwargs)

    def record(_conn, _cursor, statement, _params, _context, _many):
        """Catat statement untuk uji anggaran query."""
        calls.append(statement)

    def committed(_session):
        """Amati commit untuk membuktikan export read-only."""
        commits.append(True)

    monkeypatch.setattr(reports, "_render_pdf", render)
    event.listen(engine.sync_engine, "before_cursor_execute", record)
    event.listen(db.sync_session, "after_commit", committed)
    try:
        response = await client.get(f"/reports/class/{class_id}/pdf", headers=owner)
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", record)
        event.remove(db.sync_session, "after_commit", committed)
    assert response.status_code == 200, response.text
    queries = [call for call in calls if not call.lstrip().upper().startswith("SAVEPOINT ")]
    assert len(queries) <= 5 and all(call.lstrip().upper().startswith("SELECT") for call in queries)
    assert commits == []


@pytest.mark.parametrize("url", ["https://example.com/logo.png", "http://127.0.0.1/private", "file:///etc/passwd", "data:text/html,test"])
def test_renderer_rejects_external_resources(url):
    """Tolak resource jaringan/file dari renderer laporan."""
    from app.services.reports import reject_resource

    with pytest.raises(ValueError):
        reject_resource(url)


@pytest.mark.asyncio
async def test_class_pdf_multiple_pages_repeats_headers_and_keeps_all_rows(grading_context, monkeypatch):
    """Pertahankan baris dan header PDF lintas halaman."""
    from pypdf import PdfReader

    client, class_id, _enrollments, _components, (owner, _, _), db = grading_context
    await finalize(grading_context, monkeypatch)
    students = [Student(nim=f"MP-{index:03}", full_name=f"Mahasiswa Halaman {index:03}") for index in range(80)]
    students[12].full_name = "Nama Sangat Panjang " + "Mahasiswa " * 18
    db.add_all(students)
    await db.flush()
    enrollments = [Enrollment(class_id=uuid.UUID(class_id), student_id=student.id) for student in students]
    db.add_all(enrollments)
    await db.flush()
    db.add_all([Grade(enrollment_id=enrollment.id, final_score=Decimal("81"), status="finalized",
                      finalized_at=datetime.now(timezone.utc)) for enrollment in enrollments])
    await db.commit()
    response = await client.get(f"/reports/class/{class_id}/pdf", headers=owner)
    assert response.status_code == 200, response.text
    pages = PdfReader(io.BytesIO(response.content)).pages
    assert len(pages) > 1
    texts = [page.extract_text() for page in pages]
    assert all("NIM" in text and "Peringkat" in text and "Halaman" in text for text in texts)
    text = "\n".join(texts)
    assert all(text.count(student.nim) == 1 for student in students)


@pytest.mark.asyncio
async def test_student_component_table_can_span_pages(grading_context, monkeypatch):
    """Pertahankan rincian individu lintas halaman."""
    from pypdf import PdfReader
    from app.schemas.reports import ReportComponent
    from app.services.reports import load_student_report, render_pdf

    _client, _class_id, enrollments, _components, (owner, _, _), db = grading_context
    await finalize(grading_context, monkeypatch)
    user_id = uuid.UUID(decode_token(owner["Authorization"].split()[1])["sub"])
    report = await load_student_report(db, uuid.UUID(enrollments[0]), await db.get(User, user_id))
    report.components = [ReportComponent(id=uuid.uuid4(), name=f"Komponen-{index:03}", category="custom", weight=Decimal("1"),
                                         max_score=Decimal("100"), score=Decimal("81")) for index in range(100)]
    content = await render_pdf(report, student=True)
    texts = [page.extract_text() for page in PdfReader(io.BytesIO(content)).pages]
    assert len(texts) > 1 and all("Komponen" in text and "Bobot" in text for text in texts)
    text = "\n".join(texts)
    assert all(text.count(component.name) == 1 for component in report.components)
    assert "Nilai akhir" in text and "81,00" in text
