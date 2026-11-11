# Testing

## Backend: disposable PostgreSQL

The suite uses pytest, pytest-asyncio, and HTTPX ASGI transport. Tests may commit and remove fixtures. Use a separate disposable PostgreSQL instance. Some tests expect `admin@example.com` / `admin123`; seed those credentials only in this test environment.

From **root PowerShell**, create isolated resources without application data mounts:

```powershell
docker network create nilai-test
docker run -d --rm --name nilai-test-db --network nilai-test -e POSTGRES_PASSWORD=test-only -e POSTGRES_DB=grades_test postgres:18
docker run -d --rm --name nilai-test-redis --network nilai-test redis:7-alpine
docker exec nilai-test-db pg_isready -U postgres -d grades_test
docker exec nilai-test-redis redis-cli ping
docker build -t nilai-backend-test ./backend
```

Repeat `pg_isready` until success; require Redis `PONG`. Open a test container:

```powershell
docker run --rm -it --network nilai-test `
  -e DATABASE_URL=postgresql+asyncpg://postgres:test-only@nilai-test-db:5432/grades_test `
  -e REDIS_URL=redis://nilai-test-redis:6379/0 `
  -e JWT_SECRET=local-test-only-secret-not-for-deployment `
  -e SMTP_HOST= `
  -e SUPERADMIN_EMAIL=admin@example.com `
  -e SUPERADMIN_PASSWORD=admin123 `
  nilai-backend-test sh
```

Inside the **container POSIX shell at `/app`**:

```sh
python -m pip install -e ".[dev,seed]"
alembic upgrade head
python -c "import asyncio; from app.services.seed import seed_superadmin; asyncio.run(seed_superadmin())"
python scripts/verify_comments.py
python -m pytest
```

HTTPX ASGI transport does not execute startup lifespan, so seeding is explicit. `tests/conftest.py` adapts legacy `AsyncClient(app=...)` calls to ASGI transport. Pytest sets async mode and default test loop scope to session.

Focused runs in the same disposable container:

```sh
python -m pytest tests/test_scores.py tests/test_score_clearing.py -q
python -m pytest tests/test_finalization.py tests/test_finalization_concurrency.py -q
python -m pytest tests/test_reports.py -q
```

Exit with `exit`; clean up from **root PowerShell**:

```powershell
docker stop nilai-test-db nilai-test-redis
docker network rm nilai-test
```

The containers use `--rm`, so stopping removes their disposable data.

## Existing backend coverage

| Area | Files in `backend/tests/` |
| --- | --- |
| Identity/accounts | `test_auth.py`, `test_users.py`, `test_user_model.py` |
| Academic access/records | `test_courses.py`, `test_classes.py`, `test_students.py`, course/class model tests |
| Assessment validation | `test_components.py` |
| Scores/clearing/arithmetic | `test_scores.py`, `test_score_clearing.py` |
| Release/ranking/concurrency | `test_finalization.py`, `test_finalization_concurrency.py` |
| Read models | `test_history.py`, `test_dashboard.py` |
| Reports/delivery | `test_reports.py`, `test_notifications.py`, `test_mailer.py` |
| Infrastructure/contracts | `test_health.py`, `test_verify_comments.py`, `test_academic_ui.py` |

These include authorization, validation, conflicts, and successful operations. Report tests need PDF/workbook tooling; the image supplies native PDF dependencies. `verify_comments.py` checks PostgreSQL table/column metadata in `public`, not source comments.

## Frontend checks

From **`frontend/` in PowerShell**:

```powershell
npm ci
npm test
npm run build
npm run lint
```

Vitest runs once with jsdom, React Testing Library, shared setup/cleanup, and the Vite-compatible `@/` alias. API calls are mocked; no database is needed. Build performs TypeScript checking then Vite bundling; lint uses Oxlint.

Focused commands:

```powershell
npm test -- src/features/grades/draft.test.ts
npm test -- src/features/grades/GradeEntryGrid.test.tsx
npm test -- src/features/analytics/AnalyticsPages.test.tsx
```

Existing tests cover draft save coordination, score clearing, grade grid, analytics data/pages, notification UI, and downloads. Neither package manifest configures a coverage threshold or coverage script.

## Runtime checks

From the **repository root**:

```powershell
Invoke-RestMethod http://localhost:18000/health
docker compose --env-file .env.local --profile local ps
```

Require both `db` and `redis` true. Exercise login, class setup, draft save, release, and reports with a disposable academic dataset. HTTP 200 alone does not prove readiness. See [deployment checks](deployment.md#memeriksa-deployment) for deployed migration/worker probes.

Pytest startup guard requires explicit TEST_DATABASE_URL (PostgreSQL database ending in _test), TEST_REDIS_URL, and TEST_DATABASE_DISPOSABLE=1. It redirects DATABASE_URL/REDIS_URL before application imports. Set these values in the disposable test container above; do not direct them at a manual development dataset.
