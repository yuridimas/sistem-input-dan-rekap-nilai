# Email Notification Implementation Progress

Plan: [Sistem Input & Rekap Nilai](2026-10-24-sistem-input-rekap-nilai.md), Task 13.

## Completed

- Added Celery task `app.tasks.notifications.send_grade_release_email`, compatible with Task 11's grade-ID messages.
- Added one notification per grade: queued/sent/failed status, nullable recipient snapshot, error, sent/creation timestamps, and an internal dispatch token. Every new table/column has an Indonesian comment.
- Finalization saves queued records with grades/rankings, then publishes after commit. Broker failures mark unpublished records failed without undoing release.
- Migration `0007_notifications` backfills previous finalized grades, retaining delivery timestamps. `0008_notification_dispatch` protects overlapping publication attempts.
- Administrator APIs: `GET /admin/notifications?status=failed` (also queued/sent; omit for all) and `POST /admin/notifications/{id}/retry` returning 202 with the current record. Lecturer/unauthenticated requests return 403/401.

## Delivery and Recovery

- Empty `SMTP_HOST` logs mock delivery and marks sent, including `Grade.release_notified_at`, without opening SMTP.
- SMTP sends plain-text Indonesian course/class/final score/rank/pass-fail messages. Scores below 45 fail. Default transport is STARTTLS with certificate verification; SSL and explicit plaintext are configurable.
- One initial attempt plus three retries use delays of 1, 2, and 4 seconds. SMTP/connection failures remain queued during retries, then become failed. Missing/invalid recipients fail immediately.
- Grade/notification locks serialize duplicate deliveries. Sent records are skipped; terminal failed records need manual retry. SMTP acceptance and database commit cannot be atomic: a crash between them can still cause duplicate mail on recovery.
- Manual retry accepts failed or queued records, refreshes the current student email, resets queued state, and publishes after commit. Sent/nonexistent records return 409/404. Queued retry recovers a process crash between release commit and publication.
- Each manual retry gets a new dispatch token. An older publication failure cannot overwrite a newer attempt; automatic retries carry their generation and are ignored after replacement.
- Each synchronous task invocation creates/disposes an async engine using `NullPool` so asyncpg connections never cross event loops.

## Configuration and Local Commands

Use `.env.example`. SMTP fields: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_SECURITY` (`starttls`, `ssl`, `none`), and `SMTP_TIMEOUT` (default 10, maximum 60 seconds). Sender falls back to `SMTP_USER` when `SMTP_FROM` is empty. Leave `SMTP_HOST` empty for mock development.

Apply migrations from `backend/` using `python -m alembic upgrade head` before starting the worker. For Compose, set container hosts to `db` and `redis` in `.env.local`, then run `docker compose --profile local up --build worker`. The worker depends on healthy PostgreSQL/Redis and uses `restart: unless-stopped`. Native Windows development can use `celery -A app.celery_app:celery_app worker --pool=solo --loglevel=info` from `backend/` with localhost service settings.

## Decisions

- Nullable recipients preserve the existing optional student email behavior. Missing addresses become auditable failures; update the student email and retry as superadmin.
- Unique grade IDs reuse delivery state across retries. Dispatch tokens stay internal to persistence/task retries and are absent from API responses.
- Recovery of unqueued legacy releases is manual through queued/failed retry; no periodic dispatcher is introduced.

## Verification and Resume Point

- **127 backend tests passed**, including 20 new notification/mailer tests; one existing SlowAPI deprecation warning remains.
- Tests cover mock mode, three fake SMTP transports, content/recipient validation, eager tasks with four failing attempts, duplicate sent/failed messages, concurrent delivery/retries, stale generations, admin permissions/filtering, corrected addresses, durable broker errors, and database comments.
- A real solo Celery worker processed a message through a memory broker and persisted sent status in PostgreSQL. Initial Docker/Redis verification was blocked by unavailable services. During Task 14, Docker Desktop was started and a real Redis → Docker worker → PostgreSQL sent timestamp smoke test passed in an isolated disposable environment. No real email was sent.
- Migration upgrade succeeded through `0008_notification_dispatch`; `alembic check` is clean; Compose configuration validates the worker.
- Independent review identified a stale-enqueue race. Its deterministic regression failed before token protection and passed afterward. Worker restart policy handles Redis-disconnection exits while preserving bounded publisher retries.
- References: [Celery task retries](https://docs.celeryq.dev/en/stable/userguide/tasks.html), [SQLAlchemy event loops](https://docs.sqlalchemy.org/en/21/orm/extensions/asyncio.html#using-multiple-asyncio-event-loops).
- Task 14 is implemented; see [PDF progress](2026-10-25-pdf-progress.md). Next implementation: **Task 15 — Excel export**.
