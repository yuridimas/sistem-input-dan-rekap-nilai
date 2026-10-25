# Grade History Implementation Progress

Plan: [Sistem Input & Rekap Nilai](2026-10-24-sistem-input-rekap-nilai.md), Task 12.

## Completed

- Added `GET /students/{student_id}/history` to the grades router, with dedicated response schemas, repository queries, and a read-only assembly service.
- Only finalized grades appear. Dosen see grades from classes they currently teach; superadmins see every finalized grade for the student. This visibility policy was explicitly selected by the user.
- The repository applies lecturer ownership and finalized status before fetching grade results. Component/score details are fetched only for the selected enrollment IDs, in one batch.
- The endpoint uses at most three data queries: student existence, released grades, and component details. Authentication adds one query. No commits, recalculation, notification publication, or schema changes are introduced.

## API Contract

The response is an array whose entries contain:

- `grade_id`, `enrollment_id`, `final_score`, `rank`, and `finalized_at`.
- `course`: `id`, `code`, `name`, `credits`, and `semester`.
- `class`: `id`, `section`, and `academic_year`.
- `components`: `id`, `name`, `category`, `weight`, `max_score`, `order_index`, and `score` for each locked component.

Decimal values serialize consistently with existing grade APIs. A recorded zero remains zero. Outer joins preserve finalized rows without ranking and preserve components without a legacy score; missing values are null. Legacy null finalization timestamps are also retained.

History sorts by finalization time descending, null timestamps last, then enrollment ID ascending. Components sort by display order, creation time, then component ID.

An existing student with no visible finalized grades returns `200 []`. Missing students return 404; missing authentication returns 401; invalid UUIDs return 422. POST, PUT, PATCH, and DELETE on the history URL return 405.

## Snapshot and Access Decisions

- Reuse the component configuration and scores locked by Task 11; do not create a separate snapshot table.
- Course and class metadata reflect current records, as agreed in the plan. Their historical names/semesters are not separately frozen by this endpoint.
- Reassigning a class changes which lecturer can see that class's history, following current ownership rules.
- Missing stored ranking returns `rank: null`; never recompute ranking during a history read or silently exclude the finalized grade.

## Verification and Resume Point

- RED → GREEN: the history route initially returned 404, then passed its finalized-history integration tests.
- **107 backend tests passed**, including 11 history tests, with one existing SlowAPI deprecation warning.
- Tests cover multiple courses/semesters, lecturer/admin visibility, reassignment, draft exclusion, zero scores, missing ranking, result/detail ordering including ties, bounded SELECT queries, request errors, read-only methods, and unchanged history after rejected edits to released data.
- `alembic check` reports no new upgrade operations; no migration is required.
- Task 13 is implemented with automated worker verification; see [notification progress and pending Docker/Redis smoke test](2026-10-25-notifications-progress.md). Next implementation: **Task 14 — PDF export**.
