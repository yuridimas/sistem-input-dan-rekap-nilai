# Installation

## Prerequisites

- Git, Docker with Linux containers, and Docker Compose v2 for the full stack.
- For host development: Python 3.11+ and Node.js satisfying `^22.22.2 || ^24.15.0 || >=26.0.0`, as declared in [`package.json`](../frontend/package.json).
- PostgreSQL and Redis, supplied by Compose below.

Commands use **PowerShell** unless marked as container-shell commands. Clone using your checkout URL:

```powershell
$repositoryUrl = Read-Host 'Repository clone URL'
git clone $repositoryUrl sistem-input-dan-rekap-nilai
Set-Location sistem-input-dan-rekap-nilai
```

For an existing checkout, start in its root directory.

## Full local stack

From the **repository root**:

```powershell
Copy-Item .env.example .env.local
```

Edit `.env.local`: replace `JWT_SECRET` and `SUPERADMIN_PASSWORD`, then use container addresses:

```dotenv
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/grades
REDIS_URL=redis://redis:6379/0
```

The template starts with host addresses and needs these changes for API/worker containers. Local Compose defaults create user `postgres`, password `postgres`, and database `grades`. If changing them, set `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` and match them in `DATABASE_URL`. Use URL-safe credentials or percent-encode the password in the URL.

```powershell
docker compose --env-file .env.local --profile local config --quiet
docker compose --env-file .env.local --profile local up -d --wait db redis
docker compose --env-file .env.local --profile local run --build --rm backend alembic upgrade head
docker compose --env-file .env.local --profile local up -d --build --wait
docker compose --env-file .env.local --profile local ps
Invoke-RestMethod http://localhost:18000/health
```

Local startup requires the explicit migration. Require both dependency flags to be true, open <http://localhost:15173>, and sign in with the configured superadmin. Direct Swagger UI is <http://localhost:18000/docs>.

The seed inserts only when the email is absent and email/password are nonempty. Environment changes do not reset existing passwords. Startup suppresses seed errors; expose failures explicitly with:

```powershell
docker compose --env-file .env.local --profile local exec backend python -c "import asyncio; from app.services.seed import seed_superadmin; asyncio.run(seed_superadmin())"
```

## Environment selection

| Process | File | Database / Redis address |
| --- | --- | --- |
| Local Compose API/worker | Root `.env.local` | `db:5432`, `redis:6379` |
| Host API, working directory `backend/` | `backend/.env` or process environment | `localhost:15432`, `localhost:16379` with default Docker mappings |
| Host Vite | `frontend/.env.local` | Browser-facing API URL |
| Staging/production | `.env.staging` / `.env.prod` selected by `APP_ENV_FILE` | `db-deploy:5432`, `redis:6379` |

Compose `--env-file` supplies interpolation values; service `env_file` supplies container environment. Local API/worker services explicitly read `.env.local`. Deployment selects a file via `APP_ENV_FILE`. Shell environment can override Compose interpolation.

Pydantic reads `.env` relative to working directory and prioritizes process environment. Settings are cached per process; restart after editing. Vite requires restart in development or rebuild for deployment. Keep actual environment files out of Git.

| Setting | Purpose / default |
| --- | --- |
| `DATABASE_URL` | PostgreSQL URL using `postgresql+asyncpg` |
| `REDIS_URL` | Celery broker and Redis health probe |
| `JWT_SECRET`, `JWT_ALGORITHM` | Signing; algorithm defaults to `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS` | Defaults: 15 minutes / seven days |
| `SUPERADMIN_EMAIL`, `SUPERADMIN_PASSWORD`, `SUPERADMIN_NAME` | Idempotent bootstrap account |
| `CORS_ORIGINS` | JSON array of browser origins, including scheme/port |
| `APP_NAME`, `DEBUG` | API title and debug/SQL logging |
| `INSTITUTION_NAME` | Institution printed on reports |
| `SMTP_HOST` | Empty selects mock transport |
| `SMTP_PORT`, `SMTP_SECURITY` | Defaults: 587 / `starttls`; also supports `ssl`, `none` |
| `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | SMTP credentials and sender |
| `SMTP_TIMEOUT` | Default 10 seconds; greater than zero, at most 60 |
| `VITE_API_URL` | Public browser API base; client fallback `http://localhost:8000` |
| `DB_HOST_PORT`, `REDIS_HOST_PORT`, `BACKEND_HOST_PORT`, `FRONTEND_HOST_PORT` | Local host port overrides |
| `APP_ENV_FILE`, `DEPLOYMENT_ENV`, `HTTP_PORT`, `UVICORN_WORKERS` | Deployment selection, proxy port, process count |

`VITE_*` values are public bundle content. Mock transport may mark notifications `sent` without contacting SMTP.

## Ports

| Service | Internal | Local | Staging | Production |
| --- | --- | --- | --- | --- |
| PostgreSQL | 5432 | 15432 | 25432 | 35432 |
| Redis | 6379 | 16379 | 26379 | 36379 |
| Local API | 8000 | 18000 | Via proxy | Via proxy |
| Local Vite | 5173 | 15173 | Static assets | Static assets |
| Edge proxy | 80 | Not enabled | 28080 | 38080 |

Database, Redis, and deployment proxy bind to loopback. Container URLs use service names and internal ports. Update explicitly set `VITE_API_URL`/`CORS_ORIGINS` when overriding host ports. Native Vite/Uvicorn default to 5173/8000 and can coexist with Docker mappings.

## Backend on the host

From the **repository root**:

```powershell
docker compose --env-file .env.local --profile local up -d --wait db redis
python -m venv backend/.venv
Copy-Item .env.example backend/.env
```

Edit `backend/.env` with host URLs: `postgresql+asyncpg://postgres:postgres@localhost:15432/grades` and `redis://localhost:16379/0` for default Docker mappings. Replace secrets and bootstrap credentials. Then:

```powershell
Set-Location backend
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

POSIX activation is `source .venv/bin/activate`. Open <http://localhost:8000/docs>. PDF requires Pango, HarfBuzz, and fonts supplied by the [backend Dockerfile](../backend/Dockerfile); Docker is the documented rendering path on Windows.

Run a worker connected to the same database/Redis. From another **root PowerShell**:

```powershell
docker compose --env-file .env.local --profile local up -d --build worker
```

For a Linux/WSL host with dependencies installed, run `celery -A app.celery_app:celery_app worker --loglevel=info` from **`backend/`** in another activated shell. See the [backend guide](../backend/README.md#email-dan-worker).

## Frontend on the host

From the **repository root**:

```powershell
Set-Location frontend
npm ci
```

Create `frontend/.env.local`:

```dotenv
VITE_API_URL=http://localhost:18000
```

Use `http://localhost:8000` for a native API. From **`frontend/`**:

```powershell
npm run dev
```

Open <http://localhost:5173>. Allow that origin in backend `CORS_ORIGINS`. See [frontend development](../frontend/README.md).

## Stopping and deploying

From the **repository root**:

```powershell
docker compose --env-file .env.local --profile local down
```

Named database volumes remain. For staging/production, follow [deployment](deployment.md): separate templates/project names, migration before API/worker startup, static frontend, `/api` bundle base, and external TLS.
