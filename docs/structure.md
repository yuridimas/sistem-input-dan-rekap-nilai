# Repository structure

The tree lists versioned project files and the generated guides. Dependency folders, virtual environments, caches, build output, Git internals, and actual environment files are excluded.

```text
.
|-- backend/
|   |-- alembic/
|   |   |-- versions/
|   |   |   |-- 0002_courses.py
|   |   |   |-- 0003_classes_students_enrollments.py
|   |   |   |-- 0004_components.py
|   |   |   |-- 0005_scores_grades.py
|   |   |   |-- 0006_rankings.py
|   |   |   |-- 0007_notifications.py
|   |   |   |-- 0008_notification_dispatch.py
|   |   |   `-- a2e7676710c5_users.py
|   |   |-- env.py
|   |   `-- script.py.mako
|   |-- app/
|   |   |-- models/
|   |   |   |-- __init__.py
|   |   |   |-- class_.py
|   |   |   |-- component.py
|   |   |   |-- course.py
|   |   |   |-- enrollment.py
|   |   |   |-- grade.py
|   |   |   |-- notification.py
|   |   |   |-- ranking.py
|   |   |   |-- score.py
|   |   |   |-- student.py
|   |   |   `-- user.py
|   |   |-- repositories/
|   |   |   |-- __init__.py
|   |   |   |-- class_.py
|   |   |   |-- component.py
|   |   |   |-- course.py
|   |   |   |-- dashboard.py
|   |   |   |-- enrollment.py
|   |   |   |-- grades.py
|   |   |   |-- history.py
|   |   |   |-- notifications.py
|   |   |   |-- ranking.py
|   |   |   |-- reports.py
|   |   |   |-- scores.py
|   |   |   |-- student.py
|   |   |   `-- user.py
|   |   |-- routers/
|   |   |   |-- __init__.py
|   |   |   |-- auth.py
|   |   |   |-- classes.py
|   |   |   |-- components.py
|   |   |   |-- courses.py
|   |   |   |-- dashboard.py
|   |   |   |-- grades.py
|   |   |   |-- health.py
|   |   |   |-- notifications.py
|   |   |   |-- reports.py
|   |   |   |-- scores.py
|   |   |   |-- students.py
|   |   |   `-- users.py
|   |   |-- schemas/
|   |   |   |-- __init__.py
|   |   |   |-- auth.py
|   |   |   |-- class_.py
|   |   |   |-- component.py
|   |   |   |-- course.py
|   |   |   |-- dashboard.py
|   |   |   |-- grades.py
|   |   |   |-- history.py
|   |   |   |-- notifications.py
|   |   |   |-- reports.py
|   |   |   |-- scores.py
|   |   |   |-- student.py
|   |   |   `-- user.py
|   |   |-- services/
|   |   |   |-- __init__.py
|   |   |   |-- auth.py
|   |   |   |-- class_.py
|   |   |   |-- component.py
|   |   |   |-- component_rules.py
|   |   |   |-- course.py
|   |   |   |-- dashboard.py
|   |   |   |-- grade.py
|   |   |   |-- history.py
|   |   |   |-- mailer.py
|   |   |   |-- notifications.py
|   |   |   |-- ranking.py
|   |   |   |-- release_notifications.py
|   |   |   |-- reports.py
|   |   |   |-- scores.py
|   |   |   |-- seed.py
|   |   |   |-- student.py
|   |   |   `-- user.py
|   |   |-- tasks/
|   |   |   |-- __init__.py
|   |   |   `-- notifications.py
|   |   |-- templates/
|   |   |   |-- class_report.html
|   |   |   |-- report_base.html
|   |   |   `-- student_report.html
|   |   |-- __init__.py
|   |   |-- celery_app.py
|   |   |-- config.py
|   |   |-- database.py
|   |   |-- dependencies.py
|   |   `-- main.py
|   |-- scripts/
|   |   `-- verify_comments.py
|   |-- tests/
|   |   |-- __init__.py
|   |   |-- conftest.py
|   |   |-- test_academic_ui.py
|   |   |-- test_auth.py
|   |   |-- test_class_model.py
|   |   |-- test_classes.py
|   |   |-- test_components.py
|   |   |-- test_course_model.py
|   |   |-- test_courses.py
|   |   |-- test_dashboard.py
|   |   |-- test_finalization.py
|   |   |-- test_finalization_concurrency.py
|   |   |-- test_health.py
|   |   |-- test_history.py
|   |   |-- test_mailer.py
|   |   |-- test_notifications.py
|   |   |-- test_reports.py
|   |   |-- test_score_clearing.py
|   |   |-- test_scores.py
|   |   |-- test_students.py
|   |   |-- test_user_model.py
|   |   |-- test_users.py
|   |   `-- test_verify_comments.py
|   |-- .dockerignore
|   |-- alembic.ini
|   |-- Dockerfile
|   |-- pyproject.toml
|   `-- README.md
|-- docs/
|   |-- superpowers/
|   |   |-- plans/
|   |   |   |-- 2026-10-24-components-progress.md
|   |   |   |-- 2026-10-24-scores-progress.md
|   |   |   |-- 2026-10-24-sistem-input-rekap-nilai.md
|   |   |   |-- 2026-10-25-academic-management-progress.md
|   |   |   |-- 2026-10-25-auth-layout-progress.md
|   |   |   |-- 2026-10-25-dashboard-progress.md
|   |   |   |-- 2026-10-25-excel-progress.md
|   |   |   |-- 2026-10-25-finalization-progress.md
|   |   |   |-- 2026-10-25-grade-grid-progress.md
|   |   |   |-- 2026-10-25-history-progress.md
|   |   |   |-- 2026-10-25-notifications-progress.md
|   |   |   |-- 2026-10-25-pdf-progress.md
|   |   |   |-- 2026-10-26-analytics-progress.md
|   |   |   |-- 2026-10-26-deployment-progress.md
|   |   |   |-- 2026-10-26-export-notifications-progress.md
|   |   |   `-- 2026-10-26-final-validation-progress.md
|   |   `-- specs/
|   |       `-- 2026-10-24-sistem-input-rekap-nilai-design.md
|   |-- api.md
|   |-- architecture.md
|   |-- decisions.md
|   |-- deployment.md
|   |-- installation.md
|   |-- structure.md
|   |-- testing.md
|   `-- usage.md
|-- frontend/
|   |-- public/
|   |   |-- favicon.svg
|   |   `-- icons.svg
|   |-- src/
|   |   |-- assets/
|   |   |   |-- hero.png
|   |   |   |-- react.svg
|   |   |   `-- vite.svg
|   |   |-- components/
|   |   |   |-- ui/
|   |   |   |   |-- alert.tsx
|   |   |   |   |-- badge.tsx
|   |   |   |   |-- button.tsx
|   |   |   |   |-- dialog.tsx
|   |   |   |   |-- empty.tsx
|   |   |   |   |-- field.tsx
|   |   |   |   |-- input.tsx
|   |   |   |   |-- label.tsx
|   |   |   |   |-- native-select.tsx
|   |   |   |   |-- separator.tsx
|   |   |   |   |-- skeleton.tsx
|   |   |   |   |-- table.tsx
|   |   |   |   `-- tabs.tsx
|   |   |   |-- Layout.tsx
|   |   |   |-- PlaceholderPage.tsx
|   |   |   |-- ProtectedRoute.tsx
|   |   |   `-- Sidebar.tsx
|   |   |-- features/
|   |   |   |-- academic/
|   |   |   |   |-- api.ts
|   |   |   |   `-- Management.tsx
|   |   |   |-- analytics/
|   |   |   |   |-- AnalyticsPages.test.tsx
|   |   |   |   |-- Charts.tsx
|   |   |   |   |-- chartTokens.ts
|   |   |   |   |-- ClassAnalyticsPanel.tsx
|   |   |   |   |-- ClassCharts.tsx
|   |   |   |   |-- data.test.ts
|   |   |   |   |-- data.ts
|   |   |   |   |-- StudentDetailPage.tsx
|   |   |   |   `-- StudentTrend.tsx
|   |   |   |-- auth/
|   |   |   |   |-- LoginPage.tsx
|   |   |   |   `-- useAuth.ts
|   |   |   |-- classes/
|   |   |   |   |-- ClassDetailPage.tsx
|   |   |   |   |-- ClassDialog.tsx
|   |   |   |   `-- Roster.tsx
|   |   |   |-- components/
|   |   |   |   `-- ComponentEditor.tsx
|   |   |   |-- courses/
|   |   |   |   |-- CourseDetailPage.tsx
|   |   |   |   |-- CourseDialog.tsx
|   |   |   |   `-- CoursesPage.tsx
|   |   |   |-- dashboard/
|   |   |   |   |-- api.ts
|   |   |   |   |-- CourseOverview.tsx
|   |   |   |   `-- DashboardPage.tsx
|   |   |   |-- grades/
|   |   |   |   |-- draft.test.ts
|   |   |   |   |-- draft.ts
|   |   |   |   |-- GradeEntryGrid.test.tsx
|   |   |   |   |-- GradeEntryGrid.tsx
|   |   |   |   |-- GradeNavigationGuard.tsx
|   |   |   |   |-- hooks.ts
|   |   |   |   `-- types.ts
|   |   |   |-- notifications/
|   |   |   |   |-- NotificationsPage.test.tsx
|   |   |   |   `-- NotificationsPage.tsx
|   |   |   |-- reports/
|   |   |   |   |-- download.test.ts
|   |   |   |   |-- download.ts
|   |   |   |   |-- ReportDownloadButton.tsx
|   |   |   |   `-- StudentReportList.tsx
|   |   |   `-- students/
|   |   |       |-- StudentDialog.tsx
|   |   |       `-- StudentsPage.tsx
|   |   |-- lib/
|   |   |   |-- api.ts
|   |   |   `-- utils.ts
|   |   |-- stores/
|   |   |   `-- authStore.ts
|   |   |-- test/
|   |   |   `-- setup.ts
|   |   |-- App.css
|   |   |-- App.tsx
|   |   |-- index.css
|   |   `-- main.tsx
|   |-- .dockerignore
|   |-- .gitignore
|   |-- .oxlintrc.json
|   |-- components.json
|   |-- Dockerfile
|   |-- Dockerfile.prod
|   |-- index.html
|   |-- nginx.prod.conf
|   |-- package-lock.json
|   |-- package.json
|   |-- README.md
|   |-- tailwind.config.ts
|   |-- tsconfig.app.json
|   |-- tsconfig.json
|   |-- tsconfig.node.json
|   |-- vite.config.ts
|   `-- vitest.config.ts
|-- nginx/
|   `-- nginx.conf
|-- .env.example
|-- .env.prod.example
|-- .env.staging.example
|-- .gitignore
|-- AGENTS.md
|-- docker-compose.yml
`-- README.md

```

## Responsibilities and boundaries

| Location | Responsibility | Boundary |
| --- | --- | --- |
| `backend/app/main.py` | Compose FastAPI, middleware, lifespan, routers | Keep grading and persistence rules in lower layers. |
| `backend/app/config.py` | Cached Pydantic settings | Read environment here instead of scattering defaults. |
| `backend/app/database.py` | Async engine, session factory, request dependency | Request session does not automatically commit. |
| `backend/app/dependencies.py` | JWT identity, active account, role dependencies | Resource ownership is checked by services. |
| `backend/app/routers/` | HTTP adapters and status codes | Delegate business rules and queries. |
| `backend/app/schemas/` | Request/response contracts and field constraints | Cross-record/database validation belongs in services. |
| `backend/app/services/` | Access rules, grading, release, reports, mail transport | Inspect repository commit behavior when composing transactions. |
| `backend/app/repositories/` | SQLAlchemy query/persistence operations | Avoid duplicating business rules across repositories. |
| `backend/app/models/` | Tables, foreign keys, constraints, Indonesian metadata comments | Schema changes also require Alembic migrations. |
| `backend/app/tasks/` and `celery_app.py` | Redis-backed Celery delivery tasks | Reuse notification services rather than HTTP handlers. |
| `backend/app/templates/` | Jinja2 PDF layouts | Do not introduce external resource fetching. |
| `backend/alembic/versions/` | Incremental database migrations | Preserve applied revisions and metadata comments. |
| `backend/scripts/verify_comments.py` | PostgreSQL table/column comment verification | This checks database metadata, not Python comments. |
| `backend/tests/` | API, persistence, concurrency, report, and mail tests | Use migrated/seeded disposable PostgreSQL. |
| `frontend/src/App.tsx`, `main.tsx` | Providers, routing, mounting | Feature-specific UI belongs under features. |
| `frontend/src/features/academic/` | Shared academic API contracts/hooks and management UI | Keep HTTP session logic in the shared client. |
| `frontend/src/features/grades/` | Grade draft state, grid, release orchestration, navigation guard | Preserve pending edits across class tabs. |
| Other `frontend/src/features/` folders | Auth, courses, classes, students, components, dashboard, analytics, reports, notifications | Keep feature-owned logic near its screens. |
| `frontend/src/components/` | Layout, navigation, route guards, shared components | Business workflows remain in feature folders. |
| `frontend/src/components/ui/` | shadcn/Base UI primitives | Keep domain behavior out of primitives. |
| `frontend/src/lib/` | Shared Axios client and styling utilities | Use this client to preserve bearer/refresh behavior. |
| `frontend/src/stores/` | Zustand session persistence/hydration | Server query data uses TanStack Query. |
| `frontend/src/test/` | Vitest shared DOM setup | Tests otherwise live alongside frontend features. |
| `frontend/public/`, `frontend/src/assets/` | Public and imported static assets | Production bundles are generated into ignored `dist/`. |
| `nginx/`, frontend Nginx config | Edge API proxy and static SPA fallback | TLS termination lives outside the repository proxy. |
| `docker-compose.yml`, Dockerfiles | Local/deployment topology and images | Use profile-specific files, ports, and project names. |
| `.env*.example` | Configuration templates | Do not commit actual secrets or environment files. |
| `docs/superpowers/specs/` | Archived design specification | Check proposed behavior against current source. |
| `docs/superpowers/plans/` | Archived implementation plans/progress | Historical commands may differ from current guides. |

## Where to start

For a request flow, trace router to schema/service, then repository/model. For grade consistency, start with `services/grade.py`, `services/scores.py`, and `services/component_rules.py`. For editor state, start with `features/grades/draft.ts` and `hooks.ts`. For operations, start with [installation](installation.md), [testing](testing.md), and [deployment](deployment.md).
