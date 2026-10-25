# PDF Export Implementation Progress

Plan: [Sistem Input & Rekap Nilai](2026-10-24-sistem-input-rekap-nilai.md), Task 14.

## Completed and API Contract

- `GET /reports/student/{enrollment_id}/pdf`: individual report with student identity, course/semester/class/year, component category/weight/maximum/score, final grade, stored rank, pass/fail, and finalization time.
- `GET /reports/class/{class_id}/pdf`: summary of NIM, name, final grade, rank, and pass/fail, ordered by NIM. Detailed component columns are reserved for individual reports and later spreadsheet exports.
- User explicitly chose finalized grades only and summary class PDFs. Draft, absent grades, empty classes, or classes with any non-finalized enrollment return 409. Existing class ownership checks allow the current lecturer or superadmin; authentication/missing/invalid ID cases retain 401/403/404/422.
- Downloads use `application/pdf`, `Content-Disposition: attachment`, UUID-based filenames, and `Cache-Control: no-store`.
- Report data loading is separate from rendering and performs batched reads. No database commits, grade recalculation, or notifications occur during export.

## Presentation and Runtime

- Indonesian A4 portrait reports have repeating table headings, page numbers, wrapping names, and unbroken table rows. Scores use two decimal places with commas; values below 45 show `Tidak lulus`. Missing legacy rank/time uses an em dash.
- `INSTITUTION_NAME` supplies an optional text header; an empty value leaves the report title. No logo or external assets are used.
- Course/class metadata follow current records; scores/components/final values/ranks come from locked release data. Rendering does not reconstruct historical course names.
- Jinja autoescaping preserves literal HTML characters in names. A deny-all URL fetcher prevents HTTP, file, and data resources. Font kerning is disabled to preserve exact words in pypdf text extraction.
- Rendering runs in a thread. WeasyPrint/Jinja import lazily; missing imports/native runtime return a generic Indonesian 503 while other API routes remain available.
- Dependencies are pinned: WeasyPrint 70.0, Jinja2 3.1.6, and test-only pypdf 6.21.2. Templates are included in wheel package data and resolved relative to the installed application.
- Dockerfile installs Pango, PangoFT2, HarfBuzz subset support, and DejaVu fonts. No schema migration is introduced.

## Running Locally

Install backend dependencies with `python -m pip install -e ".[dev]"`. Configure `INSTITUTION_NAME` in the applicable env file if required.

The Docker backend image contains the native renderer. Native Windows also needs Pango; Python wheels alone are insufficient. Follow the [official WeasyPrint installation guide](https://doc.courtbouillon.org/weasyprint/latest/first_steps.html): install the MSYS2 UCRT64 Pango package and configure `WEASYPRINT_DLL_DIRECTORIES` for its DLL directory (typically `C:\msys64\ucrt64\bin`). This workstation's PDF verification used Linux/Pango in Docker rather than installing native Windows Pango.

## Verification and Resume Point

- RED → GREEN: missing endpoints; PDF extraction initially split `Tugas` because of font kerning, corrected in the shared stylesheet without weakening expected text.
- **140 backend tests passed** against disposable PostgreSQL 18 and Redis in Docker, including 13 real PDF tests. One existing SlowAPI deprecation warning remains. No PDF integration tests were replaced with mocks or skipped for missing runtime.
- PDF tests cover attachment/cache headers, data and component values, ownership, finalized-only status, draft/empty/partial classes, zero and 44.99/45 boundaries, Unicode/HTML characters, legacy placeholders, renderer 503, thread offload, query budget/read-only behavior, denied resource URLs, and multi-page tables.
- Real multi-page cases include 80 additional class rows with a long name and a 100-component individual report. Tests parse PDF text, assert every row appears once, and check repeated headings/page labels.
- Visually inspected a sample individual PDF plus first/last pages of a four-page 80-student class PDF. Preview artifacts with synthetic data are retained in this plan's ignored workspace under `task14/preview/`.
- Built a wheel and verified all three HTML templates are included. Backend Docker image built successfully, and `alembic check` reported no new upgrade operations.
- Independent review found no required changes; its suggested explicit null rank/time assertions were added and verified with focused tests.
- Follow-up Task 13 verification also succeeded: a real Redis message was consumed by a Docker Celery worker, which persisted sent status/timestamp using SMTP mock. Its previously pending Docker/Redis smoke check is resolved; no real email was sent.
- Temporary test containers and their isolated network are cleaned up after verification; local PostgreSQL data and existing user edits remain untouched.
- Next: **Task 15 — Excel export (openpyxl)**.
