# Finalization and Ranking Implementation Progress

Plan: [Sistem Input & Rekap Nilai](2026-10-24-sistem-input-rekap-nilai.md), Task 11.

## Completed

- Added atomic grade finalization and stored sequential class rankings, with migration `0006_rankings`. All new table/column comments use Bahasa Indonesia.
- Finalization takes the existing class lock, authorizes the current owner, validates components and the complete roster, and recomputes final scores using Task 10 arithmetic. Grade release metadata and rankings commit together.
- Rankings use SQL `row_number()` ordered by final score descending, NIM ascending, then name ascending. Unique constraints protect class/enrollment and class/rank pairs; rank must be positive.
- Roster changes now share the class lock. Student creation and enrollment commit together; a nested savepoint handles concurrent creation of the same NIM without releasing that lock. A failed enrollment leaves no newly created student behind.
- Extracted component configuration validation into a shared helper to avoid circular service imports.

## Public API

- `POST /classes/{id}/finalize`: no body; returns **202** with `{finalized_count, notified}`. `notified` counts broker-accepted tasks, not delivered emails.
- Missing scores return **422**, with `detail: {message, missing: [{student_nim, component_name}]}` listing every missing pair in roster/component order. Recorded zero scores are complete.
- Empty classes and invalid component configurations return **422**. Any previously finalized grade blocks repeat release with **409**.
- `GET /classes/{id}/ranking`: ordered array of `{rank, enrollment_id, student, final_score}`; an unreleased class returns `[]`.
- Both endpoints require the class lecturer or a superadmin. Missing authentication, other lecturers, and nonexistent classes return 401, 403, and 404 respectively.

## Approved Lifecycle and Notification Decisions

- User chose Task 11 only; actual email delivery, notification records, worker configuration, and retry remain Task 13.
- User chose to lock the roster after release. Adding/removing enrollments and finalizing again return 409; Task 10 already locks released scores and components.
- Publication starts only after the database commit. Each message uses task name `app.tasks.notifications.send_grade_release_email` and one string grade ID argument on the default Celery queue.
- Broker operations run in a thread with publication retries disabled and one-second connection/socket timeouts. On the first failure, publication stops, logs unqueued grade IDs, and returns the accepted count while retaining the successful release.
- Students without email remain eligible for finalization. Recipient validation belongs to Task 13. `release_notified_at` remains null until actual delivery succeeds.
- There is no durable automatic recovery between commit and queue publication yet. Task 13 must handle missed publication, delivery status, and retries. Until its worker exists, accepted messages remain queued.

## Verification and Resume Point

- RED → GREEN: missing finalize endpoint; frozen roster; failed enrollment leaving an orphan student.
- **96 backend tests passed**, with one existing SlowAPI deprecation warning. Includes 25 focused finalization/publisher/concurrency tests.
- Independent review found no required fixes. It reran the focused tests and verified real publication to an unavailable local broker failed in approximately 1.17 seconds.
- Real multi-connection tests cover two finalizers, score edits versus release, roster changes versus release, new-student transaction locking, and concurrent same-NIM creation in different classes.
- Tests cover all missing scores, zero scores, authorization, current-owner checks, shared finalization metadata, stale draft recomputation, missing grade reconstruction, ranking tie-breaks, transaction rollback, queue failure, thread offload, database comments, and post-release immutability.
- `alembic upgrade head` succeeded; `alembic check` reports no new upgrade operations.
- Task 12 is now implemented; see [history progress](2026-10-25-history-progress.md). Next: **Task 13 — Celery + Redis + email task**.
