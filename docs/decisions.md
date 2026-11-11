# Technical decisions

These choices are visible in the current implementation. Historical context is archived in [the design specification](superpowers/specs/2026-10-24-sistem-input-rekap-nilai-design.md).

## HTTP, business, and persistence layers

**Implemented:** Routers bind Pydantic contracts, services enforce access and grading rules, repositories perform SQLAlchemy operations, and models/Alembic describe schema. See [`backend/app/`](../backend/app/).

**Trade-off:** Shared validation avoids repeating grading rules in handlers. Transaction ownership varies: grading services coordinate multi-table commits, while some CRUD repositories commit directly. Inspect those boundaries before combining calls.

## PostgreSQL consistency

**Implemented:** Async SQLAlchemy/asyncpg, foreign keys, unique constraints, numeric columns, and PostgreSQL locks. A class lock serializes component/roster changes, score writes, and release. Ranking uses a window function.

**Trade-off:** Persistence and concurrency tests need PostgreSQL; SQLite does not exercise these dialect-specific semantics. The comment checker also queries PostgreSQL metadata.

## Exact arithmetic

**Implemented:** [`calculate_final_score`](../backend/app/services/grade.py) converts decimal inputs to exact fractions, then rounds half-up to two places. Missing draft entries contribute zero with full weights retained.

**Trade-off:** Repeating division cannot shift a half-cent rounding boundary. Draft totals are useful during entry, but missing scores must remain distinct from real zeroes before release.

## Complete configuration and locked releases

**Implemented:** Weights total 100% with UTS/UAS; batch create/replacement supports simultaneous weight changes. Finalization blocks score, component, and roster mutation. Scored components cannot be deleted or reduced below stored scores.

**Trade-off:** Published calculations retain assessment inputs. The API has no unfinalize flow. Course/class/student descriptive metadata is not stored as a separate immutable historical snapshot.

## Persisted unique rankings

**Implemented:** [`repositories/ranking.py`](../backend/app/repositories/ranking.py) stores `row_number` ordered by score descending, NIM ascending, then name ascending.

**Trade-off:** Equal totals have distinct positions. Reads return the release ranking rather than recalculating on every request.

## Commit release before sending email

**Implemented:** Grades, rankings, and notification records commit before Redis publication. Celery handles delivery, persistent audit supports recovery, and dispatch tokens distinguish attempts.

**Trade-off:** Broker failure does not undo released grades. HTTP 202 means queued work, not delivery. Unsent records can be retried by an admin. Database commit, enqueue, SMTP, and delivery acknowledgement remain separate failure boundaries; this is not a transactional outbox or an exactly-once mail protocol.

## Configurable mock SMTP

**Implemented:** Empty `SMTP_HOST` selects logging transport; real SMTP supports STARTTLS, SSL, or plain transport. See [`mailer.py`](../backend/app/services/mailer.py).

**Trade-off:** Local development needs no mail server, but mock success still produces `sent`. Check transport configuration when interpreting audit records.

## JWT and database identity checks

**Implemented:** bcrypt, typed access/refresh JWTs, refresh rotation, and an active-user database lookup on authenticated requests. Axios coordinates refresh; Zustand persists tokens and reloads the profile.

**Trade-off:** Deactivation/current role are checked server-side. Used refresh identifiers live in a per-process in-memory set, so replay rejection is lost on restart and not shared across API workers. Browser token storage is part of the current design.

## Dedicated draft state

**Implemented:** [`draft.ts`](../frontend/src/features/grades/draft.ts) tracks edits/saves independently of TanStack Query snapshots. Its lifecycle spans class tabs; navigation/release coordinate pending work.

**Trade-off:** Save acknowledgements do not overwrite newer typing. Server configuration changes can pause editing for reconciliation. Pending edits are in memory and should be saved before reload/exit.

## Server-rendered reports

**Implemented:** Jinja2/WeasyPrint PDF and openpyxl XLSX run in threads. Templates autoescape, PDF external fetches are blocked, XLSX text is explicit string data, and downloads use `no-store`.

**Trade-off:** Reports use authorized server data, but PDF needs native libraries/fonts. Missing dependencies return 503. Class reports require all roster results final.

## Runtime profiles and proxy

**Implemented:** Local services use bind mounts/dev servers. Deployment adds a one-shot migration dependency, static assets, dedicated database volume, and Nginx. Different project names separate staging/production resources.

**Trade-off:** Local migration is explicit. Deployment API URL `/api` is fixed at frontend build time, and TLS requires an external proxy. FastAPI currently lacks a deployment `root_path`; Swagger's schema request misses the prefix although `/api/openapi.json` is available.

## Health flags

**Implemented:** [`health.py`](../backend/app/routers/health.py) returns HTTP success with `db`/`redis` booleans; the deployment API probe checks both.

**Trade-off:** HTTP status and `status: ok` alone are insufficient for readiness.
