# Task 17: Academic Dashboard

Plan: [Sistem Input & Rekap Nilai](2026-10-24-sistem-input-rekap-nilai.md), Task 17.

## Implemented

- Added authenticated `GET /dashboard/summary` with three counts, courses and nested class summaries, and up to five recently released classes.
- Lecturers see assigned classes and their courses, regardless of the course creator. Superadmins see all courses and classes, including courses without classes. All semesters and academic years are included.
- Empty classes, missing grades, drafts, and partial finalizations count as pending. Only nonempty classes whose enrollments all have finalized grades count as released. Release time is the latest finalized timestamp; recent releases sort by time descending and ID ascending for ties. Legacy missing timestamps remain nullable and sort last.
- Course/class/student/release aggregation uses one read-only database query, plus the existing authentication query. No migrations or grade changes are needed.
- Replaced the dashboard placeholder with Indonesian summary cards, expandable course/class lists, release status badges, and recent releases that open and focus the corresponding class. Query cache keys include the current user ID.
- Added loading, empty, error/retry, keyboard interaction, reduced-motion handling, and responsive layouts. Management screens remain part of Task 18.

## Verification and Resume Point

- RED to GREEN: dashboard endpoint first returned 404; all eight dashboard tests now pass. Coverage includes role scope, missing/empty/draft/partial/released grades, duplicate-free counts, release ordering and limit, inactive/unsupported users, and constant read-only query count as classes grow.
- Full backend suite: **151 passed**, with one existing SlowAPI deprecation warning, using disposable PostgreSQL 18 and the existing Linux/Pango test image.
- `npm run build` and `rtk bypass npm run lint` passed. The existing `react(only-export-components)` warning in `components/ui/button.tsx` remains.
- Real Edge browser smoke against a separate disposable backend/database passed for both roles, account switching without stale dashboard data, course expansion by keyboard, release focus with open/closed course panels, empty data, loading, 503/retry recovery, and 320/375px layouts without horizontal overflow. No browser runtime errors were observed; desktop/mobile screenshots were inspected.
- A separate read-only review found no required changes.
- Task 18 is implemented; see [academic management progress](2026-10-25-academic-management-progress.md). Next: **Task 19 - Grade entry grid UI**.
