# Repository Guidelines

## Project Structure & Module Organization

Grade management uses FastAPI and React/TypeScript.

- `backend/app/`: HTTP routers, Pydantic schemas, business services, database repositories, and SQLAlchemy models. Preserve these layers.
- `backend/alembic/versions/`: database migrations; `backend/tests/`: API and model tests.
- `frontend/src/`: components, shared API utilities, and Zustand stores. Reusable UI lives in `components/ui/`; assets live in `src/assets/` and `public/`.
- `docs/superpowers/`: design specifications and implementation plans. Verify planned features against implementation.
- `docker-compose.yml`: PostgreSQL, Redis, and application services.

## Build, Test, and Development Commands

From the repository root:

- `docker compose up -d db redis`: start PostgreSQL and Redis.
- `docker compose --profile local up --build`: build and run all local services. Configure `.env.local` first; container connections need service hosts `db` and `redis`.

From `backend/`, use Python 3.11+ and a virtual environment:

- `python -m pip install -e ".[dev]"`: install backend and test dependencies.
- `alembic upgrade head`: apply database migrations.
- `uvicorn app.main:app --reload`: serve the API on port 8000.
- `python -m pytest`: run backend tests.

From `frontend/`:

- `npm install`: install dependencies.
- `npm run dev`: start Vite development server.
- `npm run build`: check TypeScript and create production assets.
- `npm run lint`: run Oxlint.

## Coding Style & Naming Conventions

Use four-space indentation, snake_case functions/modules, PascalCase classes, and type annotations in Python. Use two-space indentation, PascalCase React components, and camelCase functions in TypeScript. Follow nearby quotation and semicolon conventions; no formatter is configured. Prefer `@/` imports for frontend source modules. Add Alembic migrations for schema changes and preserve Indonesian database column comments.

## Testing Guidelines

Backend tests use pytest, pytest-asyncio, and HTTPX. Name files `test_*.py` and functions `test_*`. Database tests require migrated PostgreSQL; several API tests expect `admin@example.com` with password `admin123`. Configure these only in a disposable test environment. Cover authorization, validation, conflicts, and successful operations. Frontend tests use Vitest and React Testing Library (`npm test`); also run `npm run build` and `npm run lint` for UI changes.

## Commit & Pull Request Guidelines

Follow existing Conventional Commits, such as `feat(backend): courses CRUD` or `fix(backend): handle conflicts`. Keep commits focused. PRs should explain behavior changes, link relevant issues, report validation, and include screenshots for UI changes. Describe migration and configuration requirements.

## Configuration & Secrets

Start with `.env.example`. Compose reads `.env.local`; direct backend execution reads `.env` relative to its working directory or exported environment variables. Keep credentials out of commits and replace the default JWT secret.
