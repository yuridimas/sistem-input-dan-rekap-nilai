# Sistem Input & Rekap Nilai — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a lecturer-facing grade input and recap system (FastAPI + React) covering all 10 features, deployed via Docker (local/staging/prod), with Bahasa Indonesia UI and DB comments.

**Architecture:** Modular monolith. Single FastAPI backend organized into domain modules (auth, users, courses, classes, students, components, grades, ranking, notifications, reports) + single React SPA with feature folders. PostgreSQL 18, Celery + Redis for async email. Docker Compose with profiles.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2, Celery + Redis, WeasyPrint, openpyxl, bcrypt, python-jose. React + Vite + TypeScript + Tailwind + shadcn/ui + Recharts + TanStack Query + Zustand. PostgreSQL 18.

**Spec:** `docs/superpowers/specs/2026-10-24-sistem-input-rekap-nilai-design.md`

## Global Constraints

**Resume status (2026-10-25):** Tasks 1–14 are implemented. Task 14 passed 140 backend tests with real Linux/Pango PDF rendering; Task 13's pending Docker/Redis worker smoke check also passed. See [component progress](2026-10-24-components-progress.md), [score entry progress](2026-10-24-scores-progress.md), [finalization progress](2026-10-25-finalization-progress.md), [history progress](2026-10-25-history-progress.md), [notification progress](2026-10-25-notifications-progress.md), and [PDF progress](2026-10-25-pdf-progress.md). Resume with **Task 15**. Original step checkboxes below are retained as the execution template.

- Version floors: Python 3.11+, Node 20+, PostgreSQL 18, latest major for all libraries — verify installed versions before execution and pin exact majors in lockfiles.
- Mono repo layout: `backend/` (FastAPI) and `frontend/` (React). All backend paths are under `backend/`, all frontend under `frontend/`.
- Every DB table and column MUST have a Bahasa Indonesia `COMMENT` (SQLAlchemy `comment=`, Alembic `COMMENT ON`).
- UI copy in Bahasa Indonesia.
- Numeric scores only; fail if final < 45.
- Components: must include ≥1 UTS and ≥1 UAS; weights sum to exactly 100 per class; weight > 0.
- Finalized grades are immutable (no edits after release).
- Ranking: sequential (1..N, ties broken by NIM then name), not shared ranks.
- Async email via Celery; dev uses mock logger, prod uses SMTP from env.
- No GitHub Actions CI; tests run manually.
- Auth: JWT access 15 min + refresh 7 d, bcrypt cost 12, login rate-limited.

## Review Focus

1. Weight sum floating-point tolerance — a sum of 99.9999 must be rejected; use Decimal and exact equality to 100.00.
2. Finalize with missing scores must return 422 listing every missing (student, component), not just the first.
3. Email delivery failure must never block or fail the release request; status tracked in `notifications`.
4. Ranking ties must be sequential (row_number), not `RANK()`/`DENSE_RANK()` shared positions.
5. Concurrent score edits: last-write-wins is acceptable, but `updated_at` must reflect the latest write and audit who entered it.

---

## Phase 0 — Scaffolding

### Task 1: Backend project skeleton

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`
- Create: `backend/app/dependencies.py`
- Create: `backend/app/routers/health.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/alembic.ini`, `backend/alembic/env.py`

**Interfaces:**
- Produces: `get_settings() -> Settings`, `get_db() -> AsyncSession`, `app` (FastAPI instance), `GET /health` returning `{"status","db","redis"}`.

- [ ] **Step 1: Write failing test** `backend/tests/test_health.py`

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_health_ok():
    async with AsyncClient(app=app, base_url="http://test") as c:
        r = await c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
```

- [ ] **Step 2: Run test to verify it fails** — `cd backend && pytest tests/test_health.py -v` → FAIL (module not found).
- [ ] **Step 3: Implement skeleton.** pyproject with FastAPI, SQLAlchemy[asyncio], asyncpg, pydantic-settings, alembic, celery, redis, httpx, pytest, pytest-asyncio. `config.py`: pydantic-settings `Settings` reading env. `database.py`: async engine + `AsyncSessionLocal` + `get_db`. `main.py`: FastAPI app, include health router, CORS from settings. `health.py`: ping DB + Redis.
- [ ] **Step 4: Run test** → PASS.
- [ ] **Step 5: Commit** `git commit -m "feat(backend): project skeleton + health endpoint"`.

### Task 2: Frontend project skeleton

**Files:**
- Create: `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tsconfig.json`
- Create: `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/lib/api.ts`, `frontend/src/index.css`
- Create: `frontend/tailwind.config.ts`, `frontend/components.json` (shadcn)

**Interfaces:**
- Produces: `api` axios/fetch client with base URL from `VITE_API_URL` and auth interceptor; `App` with router.

- [ ] **Step 1: Scaffold with Vite** — `npm create vite@latest frontend -- --template react-ts` (run in repo root, then move config).
- [ ] **Step 2: Install deps** — tailwindcss, shadcn/ui init, react-router-dom, @tanstack/react-query, zustand, recharts, axios.
- [ ] **Step 3: Configure Tailwind + shadcn** (components.json, index.css with CSS vars).
- [ ] **Step 4: Implement `lib/api.ts`** — fetch wrapper attaching `Authorization: Bearer <token>` from auth store; base URL from env.
- [ ] **Step 5: App.tsx** — QueryClientProvider + BrowserRouter with placeholder routes.
- [ ] **Step 6: Verify** — `npm run dev` starts without errors; `npm run build` succeeds.
- [ ] **Step 7: Commit** `git commit -m "feat(frontend): vite + tailwind + shadcn skeleton"`.

### Task 3: Docker compose (local profile)

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.local`, `.env.example`
- Create: `backend/Dockerfile`, `frontend/Dockerfile`

**Interfaces:**
- Produces: `docker compose --profile local up` starts postgres:18, redis, backend (hot reload), frontend (vite dev).

- [ ] **Step 1: Write compose** with services `db` (postgres:18, volume, healthcheck), `redis`, `backend` (build, env_file .env.local, volume mount for hot reload, depends_on db/redis), `frontend` (build, env_file, volume). Profile `local`.
- [ ] **Step 2: Dockerfiles** — backend: python:3.11-slim, install deps, uvicorn --reload. frontend: node:20, npm install, vite dev.
- [ ] **Step 3: .env.local** with DATABASE_URL, REDIS_URL, JWT_SECRET, SMTP_* (empty for dev mock), SUPERADMIN_EMAIL/PASSWORD.
- [ ] **Step 4: Verify** — `docker compose --profile local up -d` → all healthy; `curl localhost:8000/health` ok.
- [ ] **Step 5: Commit** `git commit -m "chore: docker compose local profile"`.

---

## Phase 1 — Auth & Users

### Task 4: User model + Alembic baseline + seed superadmin

**Files:**
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/alembic/versions/0001_users.py`
- Create: `backend/app/services/seed.py`

**Interfaces:**
- Produces: `User` model (id, email, password_hash, full_name, role, is_active, timestamps) with Bahasa comments. `seed_superadmin()` creates superadmin from env if none exists.

- [ ] **Step 1: Write test** `backend/tests/test_user_model.py` — insert user, assert fields + comment presence in `information_schema.columns` (optional).
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement User model** with `comment=` on every column. Role enum `superadmin|lecturer`.
- [ ] **Step 4: Generate migration** `alembic revision --autogenerate -m "users"`; review; ensure comments emitted.
- [ ] **Step 5: Implement seed_superadmin** (idempotent).
- [ ] **Step 6: Run migration + seed** in local container; verify.
- [ ] **Step 7: Commit**.

### Task 5: Auth (login, JWT, refresh, role guards)

**Files:**
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/services/auth.py`
- Create: `backend/app/routers/auth.py`
- Create: `backend/app/dependencies.py` additions (`get_current_user`, `require_role`)
- Modify: `backend/app/main.py` (include router)

**Interfaces:**
- Consumes: `User`, `get_db`.
- Produces: `POST /auth/login` → `{access_token, refresh_token}`; `POST /auth/refresh`; `GET /auth/me`; `get_current_user(db, token) -> User`; `require_role(*roles)` dependency.

- [ ] **Step 1: Test login success/failure** — `tests/test_auth.py`: valid creds → 200 + tokens; bad creds → 401; missing → 422.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** password verify (bcrypt), JWT encode/decode (python-jose), refresh rotation. Rate limit login via slowapi.
- [ ] **Step 4: Test role guard** — lecturer token on superadmin endpoint → 403.
- [ ] **Step 5: Run** → PASS.
- [ ] **Step 6: Commit**.

### Task 6: User management (lecturer CRUD)

**Files:**
- Create: `backend/app/schemas/user.py`
- Create: `backend/app/repositories/user.py`
- Create: `backend/app/services/user.py`
- Create: `backend/app/routers/users.py`

**Interfaces:**
- `POST /admin/users` (superadmin) create lecturer; `GET /admin/users`; `GET/PATCH/DELETE /admin/users/{id}`. Duplicate email → 409.

- [ ] **Step 1: Tests** — create/list/get/update/deactivate lecturer; non-superadmin → 403; duplicate email → 409.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** repository + service + router with role guard.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit**.

---

## Phase 2 — Academic Core

### Task 7: Courses CRUD

**Files:**
- Create: `backend/app/models/course.py`
- Create: migration `0002_courses.py`
- Create: `backend/app/schemas/course.py`, `repositories/course.py`, `services/course.py`, `routers/courses.py`

**Interfaces:**
- `Course` (id, code unique, name, credits, semester, created_by, created_at). Endpoints under `/courses` (lecturer sees own-created? superadmin all). `GET /courses`, `POST`, `GET/{id}`, `PATCH/{id}`, `DELETE/{id}`. Duplicate code → 409.

- [ ] **Step 1: Test** course CRUD + duplicate code 409.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** model with comments, migration, repo/service/router.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit**.

### Task 8: Classes, enrollments, students

**Files:**
- Create: `backend/app/models/student.py`, `class_.py`, `enrollment.py`
- Create: migration `0003_classes_students_enrollments.py`
- Create: schemas/repositories/services/routers for `students`, `classes`

**Interfaces:**
- `Student` (id, nim unique, full_name, email). `Class` (id, course_id, section, lecturer_id, academic_year). `Enrollment` (id, class_id, student_id). Endpoints: `/students` CRUD; `/classes` CRUD; `POST /classes/{id}/enrollments` (add student by nim, create student if not exists); `GET /classes/{id}/roster`; `DELETE /classes/{id}/enrollments/{enrollment_id}`.

- [ ] **Step 1: Tests** — create class, enroll student (new + existing), roster returns students, duplicate enrollment → 409, delete enrollment.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement**.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit**.

### Task 9: Grade components

**Files:**
- Create: `backend/app/models/component.py`
- Create: migration `0004_components.py`
- Create: schemas/repositories/services/routers `components.py`

**Interfaces:**
- `Component` (id, class_id, name, category enum tugas/uts/uas/custom, weight Decimal, max_score, order_index). Endpoints: `GET/POST /classes/{id}/components`, `PATCH/DELETE /components/{id}`. Service validates: ≥1 UTS and ≥1 UAS; sum weights == 100.00 (Decimal exact); weight > 0. Violations → 422 with detail.

- [ ] **Step 1: Test weight validation** — sum 99.99 → 422; missing UTS → 422; valid set → 201; weight 0 → 422.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** with Decimal; validation in service (not just DB).
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit**.

---

## Phase 3 — Grades & Ranking

### Task 10: Score entry + auto final score (draft)

**Files:**
- Create: `backend/app/models/score.py`, `grade.py`
- Create: migration `0005_scores_grades.py`
- Create: schemas/repositories/services/routers `scores.py`, `grades.py`

**Interfaces:**
- `Score` (id, enrollment_id, component_id, score, entered_by, entered_at, updated_at). `Grade` (id, enrollment_id unique, final_score, status draft/finalized, finalized_at, finalized_by, release_notified_at).
- `PUT /enrollments/{id}/scores` body `{component_id: score}` upserts scores, recomputes `Grade.final_score` (weighted sum) with status draft. Validates score range. Returns updated grade.
- `GET /classes/{id}/grades` returns roster with components + final + status.

- [ ] **Step 1: Test** — enter scores → final computed correctly (e.g. tugas 80*0.3 + uts 70*0.3 + uas 90*0.4 = 81); out-of-range → 422; re-enter updates.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** upsert + recompute final (Decimal). Create Grade row if missing.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit**.

### Task 11: Finalize + ranking

**Files:**
- Modify: `backend/app/services/grade.py`
- Create: `backend/app/services/ranking.py`
- Create: `backend/app/models/ranking.py`
- Create: migration `0006_rankings.py`
- Modify: `backend/app/routers/grades.py` (add finalize endpoint)

**Interfaces:**
- `POST /classes/{id}/finalize` → validates all enrollments have all component scores (else 422 listing missing), sets status=finalized, finalized_at, finalized_by, computes sequential ranking (sort final desc, ties by NIM then name, assign 1..N), enqueues notification task per enrollment, returns `{finalized_count, notified}`.
- `GET /classes/{id}/ranking` returns ordered list with rank.

- [ ] **Step 1: Test finalize blocked** — missing score → 422 with list of `{student_nim, component_name}`.
- [ ] **Step 2: Test finalize success** — status finalized, ranking sequential with ties handled.
- [ ] **Step 3: Test ranking tie-break** — two students same final → ranks sequential by NIM.
- [ ] **Step 4: Run** → FAIL.
- [ ] **Step 5: Implement** validation + finalize + ranking (row_number ordering). Enqueue Celery task (stubbed in tests via eager mode).
- [ ] **Step 6: Run** → PASS.
- [ ] **Step 7: Commit**.

### Task 12: Grade history (read-only)

**Files:**
- Modify: `backend/app/routers/grades.py` (add history endpoint)
- Create: `backend/app/schemas/history.py`

**Interfaces:**
- `GET /students/{id}/history` → list of finalized grades across classes/courses/semesters with final_score, rank, components snapshot. No edit endpoints (405/404 if attempted).

- [ ] **Step 1: Test** — history returns finalized only; draft excluded; no PUT/PATCH route → 405.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement**.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit**.

---

## Phase 4 — Notifications

### Task 13: Celery + Redis + email task

**Files:**
- Create: `backend/app/celery_app.py`
- Create: `backend/app/tasks/notifications.py`
- Create: `backend/app/models/notification.py`
- Create: migration `0007_notifications.py`
- Create: `backend/app/services/mailer.py`
- Modify: `docker-compose.yml` (add worker service)

**Interfaces:**
- `send_grade_release_email(grade_id)` Celery task. Mailer: if SMTP_HOST empty → mock (log + mark sent); else SMTP. Retries 3× backoff. On failure → `notifications.status=failed`, `error_message`. `notifications` table tracks queued/sent/failed.
- `GET /admin/notifications?status=failed` list; `POST /admin/notifications/{id}/retry`.

- [ ] **Step 1: Test mailer mock** — calling task in eager mode creates notification row with status sent and no SMTP call.
- [ ] **Step 2: Test failure path** — force SMTP error → status failed + error_message; retry re-queues.
- [ ] **Step 3: Run** → FAIL.
- [ ] **Step 4: Implement** celery app, task, mailer abstraction, model, migration, endpoints.
- [ ] **Step 5: Add worker to compose**; verify `docker compose up worker` processes a queued task.
- [ ] **Step 6: Run** → PASS.
- [ ] **Step 7: Commit**.

---

## Phase 5 — Reports

### Task 14: PDF export (WeasyPrint)

**Files:**
- Create: `backend/app/services/reports.py`
- Create: `backend/app/routers/reports.py`
- Create: `backend/app/templates/student_report.html` (Jinja2)

**Interfaces:**
- `GET /reports/student/{enrollment_id}/pdf` → PDF bytes (Content-Type application/pdf, Content-Disposition attachment). Template: institution header (from env), student info, component table, final, rank, pass/fail.
- `GET /reports/class/{class_id}/pdf` → class roster PDF.

- [ ] **Step 1: Test** — endpoint returns 200, content-type pdf, non-empty bytes, contains student name (parse text).
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** Jinja2 template + WeasyPrint render. Handle missing WeasyPrint system deps in Dockerfile (install libpango etc.).
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit**.

### Task 15: Excel export (openpyxl)

**Files:**
- Modify: `backend/app/services/reports.py`
- Modify: `backend/app/routers/reports.py`

**Interfaces:**
- `GET /reports/class/{class_id}/xlsx` → xlsx bytes (Content-Type application/vnd.openxmlformats-officedocument.spreadsheetml.sheet). Sheet: roster rows with NIM, name, each component score, final, rank, pass/fail. Header styled.

- [ ] **Step 1: Test** — endpoint returns 200, parse with openpyxl, assert header + row count + values.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement**.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit**.

---

## Phase 6 — Frontend

### Task 16: Auth pages + protected routes + layout

**Files:**
- Create: `frontend/src/features/auth/*` (LoginPage, authStore, useAuth)
- Create: `frontend/src/components/Layout.tsx`, `Sidebar.tsx`, `ProtectedRoute.tsx`

**Interfaces:**
- Login form → calls `/auth/login`, stores tokens, redirects to dashboard. Protected routes redirect to /login if no token. Role-based menu (superadmin sees users/courses all; lecturer sees own).

- [ ] **Step 1: Implement auth store** (zustand) with token persistence.
- [ ] **Step 2: Login page** with form + error display (Bahasa).
- [ ] **Step 3: ProtectedRoute + layout**.
- [ ] **Step 4: Verify** manual login flow against backend.
- [ ] **Step 5: Commit**.

### Task 17: Dashboard

**Files:**
- Create: `frontend/src/features/dashboard/*`

**Interfaces:**
- `GET /dashboard/summary` backend endpoint (add to a new `dashboard` router) returning courses taught, class count, pending (draft) classes, recently released. Frontend renders summary cards + drill-down links.

- [ ] **Step 1: Backend** — add `dashboard` router + service; test summary counts.
- [ ] **Step 2: Frontend** — summary cards, course list with drill-down to classes.
- [ ] **Step 3: Verify** manual.
- [ ] **Step 4: Commit**.

### Task 18: Courses/Classes/Students/Components management UI

**Files:**
- Create: `frontend/src/features/courses/*`, `classes/*`, `students/*`, `components/*`

**Interfaces:**
- CRUD screens with forms, tables, validation messages (Bahasa). Component editor shows weight sum indicator and enforces UTS/UAS.

- [ ] **Step 1: Implement course list + create/edit dialog.**
- [ ] **Step 2: Class management + roster enrollment (add by NIM).**
- [ ] **Step 3: Student list.**
- [ ] **Step 4: Component editor with live weight sum.**
- [ ] **Step 5: Verify** manual end-to-end.
- [ ] **Step 6: Commit**.

### Task 19: Grade entry grid UI

**Files:**
- Create: `frontend/src/features/grades/GradeEntryGrid.tsx`, `hooks.ts`

**Interfaces:**
- Table: rows students, columns components, editable cells with validation, auto-final column (read-only), draft/finalized badge, "Finalisasi & Rilis" button with confirmation dialog showing missing-score check result.

- [ ] **Step 1: Implement grid** with TanStack Query fetch + optimistic local state.
- [ ] **Step 2: Save draft** on blur/submit.
- [ ] **Step 3: Finalize flow** with error display for missing scores.
- [ ] **Step 4: Verify** manual.
- [ ] **Step 5: Commit**.

### Task 20: Charts (Recharts)

**Files:**
- Create: `frontend/src/features/grades/Charts.tsx` or `features/analytics/*`

**Interfaces:**
- Student trend line chart, class distribution bar chart, component breakdown stacked bar. Data from `GET /classes/{id}/grades` + history endpoint.

- [ ] **Step 1: Implement three charts.**
- [ ] **Step 2: Verify** rendering with sample data.
- [ ] **Step 3: Commit**.

### Task 21: Export UI + notifications status

**Files:**
- Create: `frontend/src/features/reports/*`, `frontend/src/features/notifications/*`

**Interfaces:**
- Export buttons trigger download (PDF/XLSX) via backend URLs. Superadmin view for failed notifications + retry.

- [ ] **Step 1: Implement export buttons with download handling.**
- [ ] **Step 2: Implement notifications status view (superadmin).**
- [ ] **Step 3: Verify** manual.
- [ ] **Step 4: Commit**.

---

## Phase 7 — Polish & Deploy

### Task 22: Docker staging/prod profiles + nginx

**Files:**
- Modify: `docker-compose.yml` (add staging/prod profiles, nginx service)
- Create: `nginx/nginx.conf`, `frontend/Dockerfile.prod`

**Interfaces:**
- `docker compose --profile staging up` and `--profile prod up` work; healthchecks pass; TLS placeholder documented.

- [ ] **Step 1: Add profiles** with production Dockerfiles (backend gunicorn/uvicorn workers, frontend built static).
- [ ] **Step 2: nginx config** reverse proxy + static serving.
- [ ] **Step 3: Verify** staging profile boots and `/health` ok.
- [ ] **Step 4: Commit**.

### Task 23: DB comments verification + seed data + README

**Files:**
- Create: `backend/scripts/verify_comments.py`
- Create: `README.md`

**Interfaces:**
- Script queries `information_schema` and asserts every table/column has non-null comment. README documents setup, env vars, docker profiles, test commands.

- [ ] **Step 1: Write verification script** and run → all pass.
- [ ] **Step 2: Write README** (Bahasa Indonesia + English setup).
- [ ] **Step 3: Final manual smoke test** of all 10 features on local profile.
- [ ] **Step 4: Commit**.

---

## Self-Review Notes

- Spec coverage: all 10 features mapped to tasks (1–10 → Tasks 10,11,14/15,17,9,12,13,11,17). Auth/users (Task 4–6), infra (1–3,22), frontend (16–21), polish (23).
- Type consistency: signatures defined in Interfaces blocks; implementers must match. Key names: `final_score`, `status`, `rank`, `weight`, `max_score`, `category` (tugas/uts/uas/custom).
- Review Focus items (5) each have a test in the owning task: weight tolerance (Task 9), missing scores (Task 11), email non-blocking (Task 13), sequential ranking (Task 11), updated_at/entered_by (Task 10).
- Proportion: plan is longer than spec but each step is a checkable action, not a code transcript; bodies omitted except where algorithm is non-obvious.
