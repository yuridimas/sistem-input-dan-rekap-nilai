# Task 19: Grade Entry Grid and Finalization

Plan: [Sistem Input & Rekap Nilai](2026-10-24-sistem-input-rekap-nilai.md), Task 19.

## Implemented

- Added the protected `?tab=grades` class view: roster/component grid, range/two-decimal validation, empty-versus-zero semantics, backend-calculated final scores, and draft/finalized status. Decimal commas are accepted in the UI. Mobile tables scroll horizontally inside their container.
- Expanded score PUT payloads to accept null as deletion of a draft score. Omitted scores remain untouched. Deletion/upsert validates the complete payload, uses the existing class/enrollment locks, and recalculates the draft total in one transaction. Finalized grades remain immutable; no migration is needed.
- Autosave runs on blur with a serialized class queue and per-cell versions. Save all explicitly retries failures and flushes newer edits; older responses cannot replace newer typing. Dirty cells survive background refreshes and tab changes. Structural roster/component changes pause writes until an explicit reload/discard.
- Finalization first flushes writes and refreshes server data, then displays a confirmation and focusable missing-score list. Only explicit confirmation submits release. Successful release refreshes class/grade/dashboard state; notification counts describe queued messages rather than delivered email.
- Uncertain release responses require a server-status check before retry. Concurrent finalization adopts authoritative read-only values. Partially finalized classes retain editable draft rows while class re-finalization stays disabled, matching the backend.
- Migrated existing routes to the React Router data router for navigation blocking. Dirty/in-flight drafts receive leave-page protection; browser refresh/close warns, and authentication redirects remain available.

## Tooling and Verification

- Added `npm test` with Vitest 5, React Testing Library, user-event, jest-dom, and jsdom 30. Current tooling requires Node `^22.22.2 || ^24.15.0 || >=26.0.0`; the frontend Docker image now uses Node 24. Local verification used Node 24.20.0.
- Backend RED to GREEN covered draft clearing, mixed delete/upsert, zero/omitted values, atomic rejection, access, missing-score finalization, and finalized protections. The former null-is-invalid test case was updated for the approved contract. Full Linux/Pango backend suite: **162 passed**, one existing SlowAPI deprecation warning.
- Frontend: **22 tests passed**, covering queued versions, delayed acknowledgements, failures/retry, stale refreshes, structural pauses, detach, tab retention, missing-score confirmation, uncertain release, and navigation protection. Build and lint passed; only the existing button Fast Refresh warning remains.
- The updated Node 24 frontend Docker image built successfully and ran all **22 frontend tests** successfully in Linux.
- A fresh review found three races: metadata errors unmounted the draft guard, failed writes cleared a structural pause, and structurally shared post-save data could remain ignored. All three were reproduced with failing tests and fixed; the full frontend suite passed afterward.
- Real Edge smoke against a disposable backend/database passed delayed-response editing, failed-save retry, comma decimals, range/zero/clearing, exact backend rounding, missing-score focus, dirty navigation, tab retention, structural reload, release locking, uncertain-response checks without duplicate POST, admin/lecturer access, and 320/375px layouts. No runtime exceptions were observed; desktop/mobile screenshots were inspected.
- Existing user changes to the student router and class tests, untracked AGENTS.md, and egg-info remain outside this task's commit.
- Task 20 charts are implemented and verified; see [analytics progress](2026-10-26-analytics-progress.md). Next: **Task 21 — Export UI and notification status**.
