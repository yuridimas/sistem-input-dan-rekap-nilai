# Excel Export Progress

Plan: [Sistem Input & Rekap Nilai](2026-10-24-sistem-input-rekap-nilai.md), Task 15.

## API and Workbook

- `GET /reports/class/{class_id}/xlsx` exports a class roster for its lecturer or a superadmin. All grades must be finalized; empty, draft, or partially finalized classes return 409, consistent with the PDF export.
- The `Rekap Kelas` sheet contains NIM, name, one raw-score column per component, final score, stored rank, and pass/fail. Component headers include name, category, weight, and maximum score. Students are ordered by NIM.
- XLSX downloads use the official spreadsheet MIME type, a class-ID filename, and `Cache-Control: no-store`.
- Header cells use a dark fill and bold white text; score columns use two decimals, the header is frozen, and filtering covers the full table. Text values are explicitly stored as text so user-controlled names or NIMs cannot become spreadsheet formulas.
- Component data is loaded in one batch, rendering runs in a worker thread, and exports remain read-only. `openpyxl==3.1.5` is a runtime dependency. No schema migration is needed.

## Verification and Resume Point

- RED to GREEN: the new endpoint first returned 404; it now returns an XLSX workbook parsed by openpyxl.
- Sixteen report tests passed, covering XLSX content, dynamic component columns, formula-like names, zero scores, missing rank, pass/fail boundary, authorization, final-only errors, off-thread rendering, query budget, and read-only behavior alongside existing PDF coverage.
- Full backend suite: **143 passed**, one existing SlowAPI deprecation warning. Tests ran with disposable PostgreSQL and the disposable test admin credentials required by existing auth tests.
- Next: **Task 16 — auth pages, protected routes, and layout**.
