# Task 22: Docker Staging/Production Profiles and Nginx

Plan: [Sistem Input & Rekap Nilai](2026-10-24-sistem-input-rekap-nilai.md), Task 22.

## Implemented

- Kept the local Compose services and added staging/prod deployment services: a separate PostgreSQL service, one-shot Alembic migration, Uvicorn API workers, Celery worker, static frontend, and edge Nginx. API and worker wait for successful migration; API health requires both PostgreSQL and Redis to respond. The deployment database requires an explicit `DEPLOYMENT_ENV=staging|prod`, so it cannot start from local settings.
- Added a multi-stage frontend image using Node 24 and Nginx 1.31, with SPA deep-link fallback and `/api` as its build-time API base.
- Added edge Nginx routing: `/api/*` proxies to FastAPI with the prefix removed; other requests go to the static frontend. The edge port binds to loopback for a host-local TLS terminator, and forwarded protocol headers are passed through.
- Added staging/prod environment templates, ignored runtime env filenames, and excluded environment files from backend/frontend build contexts.
- PostgreSQL and Redis ports bind only to loopback. Use distinct Compose project names so staging and prod have separate networks and volumes.

## Verification and Resume Point

- `docker compose --profile local config --quiet` passed.
- Staging and prod `config --quiet` passed using their example environment templates.
- Both staging and prod were built and started with `docker compose up --build --wait` under separate project names. `/api/health` returned DB and Redis healthy, SPA deep links returned the app shell, and `nginx -t` passed in each edge proxy.
- Starting the deploy database without deployment environment settings failed as expected, even though Compose otherwise defaults service env files to `.env.local`.
- The disposable verification containers, networks, and database volumes were removed after smoke checks. No real `.env.staging` or `.env.prod` was created; copy the templates and replace all placeholders before deployment.
- `frontend/Dockerfile.prod` builds successfully. Docker image tags were confirmed against [Node](https://hub.docker.com/_/node) and [Nginx](https://hub.docker.com/_/nginx) official image listings.
- Next: **Task 23 — DB comments verification, seed data, and README**.
