# Struktur repository

Tree berikut mencantumkan file proyek dan panduan dokumentasi. Folder dependensi, virtual environment, cache, hasil build, internal Git, serta file environment aktual tidak disertakan.

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
|   |   |-- seeding/
|   |   |   |-- __init__.py
|   |   |   |-- __main__.py
|   |   |   |-- config.py
|   |   |   |-- dataset.py
|   |   |   |-- factories.py
|   |   |   |-- manifest.py
|   |   |   `-- scenarios.py
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
|   |   |-- support/
|   |   |   |-- __init__.py
|   |   |   |-- database_guard.py
|   |   |   `-- seed_data.py
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
|   |   |-- test_seed_cli.py
|   |   |-- test_seed_generation.py
|   |   |-- test_seed_persistence.py
|   |   |-- test_seed_scenarios.py
|   |   |-- test_students.py
|   |   |-- test_test_database_guard.py
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
|   |   |   |-- 2026-10-26-final-validation-progress.md
|   |   |   |-- 2026-11-05-dummy-seeding.md
|   |   |   |-- 2026-11-05-frontend-data-table-dashboard-session-ui.md
|   |   |   |-- 2026-11-05-multicourse-seeding.md
|   |   |   |-- 2026-11-05-users-page.md
|   |   |   |-- 2026-11-11-course-class-index-flow.md
|   |   |   `-- 2026-11-11-feature-index-page-standardization.md
|   |   `-- specs/
|   |       |-- 2026-10-24-sistem-input-rekap-nilai-design.md
|   |       |-- 2026-11-05-dummy-seeding-design.md
|   |       |-- 2026-11-05-users-page-design.md
|   |       `-- 2026-11-11-course-class-index-design.md
|   |-- api.md
|   |-- architecture.md
|   |-- decisions.md
|   |-- deployment.md
|   |-- installation.md
|   |-- seeding.md
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
|   |   |   |-- data-table/
|   |   |   |   |-- DataTable.test.tsx
|   |   |   |   |-- DataTable.tsx
|   |   |   |   |-- DataTablePagination.tsx
|   |   |   |   |-- DataTableToolbar.tsx
|   |   |   |   `-- index.ts
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
|   |   |   |-- Layout.test.tsx
|   |   |   |-- Layout.tsx
|   |   |   |-- PageBreadcrumbs.test.tsx
|   |   |   |-- PageBreadcrumbs.tsx
|   |   |   |-- PlaceholderPage.tsx
|   |   |   |-- ProtectedRoute.tsx
|   |   |   |-- SessionProfile.tsx
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
|   |   |   |   |-- Roster.test.tsx
|   |   |   |   `-- Roster.tsx
|   |   |   |-- components/
|   |   |   |   `-- ComponentEditor.tsx
|   |   |   |-- courses/
|   |   |   |   |-- CourseClassesTable.test.tsx
|   |   |   |   |-- CourseClassesTable.tsx
|   |   |   |   |-- CourseClassFlow.test.tsx
|   |   |   |   |-- CourseDetailPage.test.tsx
|   |   |   |   |-- CourseDetailPage.tsx
|   |   |   |   |-- CourseDialog.tsx
|   |   |   |   |-- CoursesPage.test.tsx
|   |   |   |   `-- CoursesPage.tsx
|   |   |   |-- dashboard/
|   |   |   |   |-- api.ts
|   |   |   |   |-- CourseOverview.tsx
|   |   |   |   |-- DashboardPage.test.tsx
|   |   |   |   |-- DashboardPage.tsx
|   |   |   |   |-- DashboardWidgets.test.tsx
|   |   |   |   |-- RecentReleases.tsx
|   |   |   |   `-- SummaryCards.tsx
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
|   |   |   |-- students/
|   |   |   |   |-- StudentDialog.tsx
|   |   |   |   |-- StudentsPage.test.tsx
|   |   |   |   `-- StudentsPage.tsx
|   |   |   |-- users/
|   |   |   |   |-- types.ts
|   |   |   |   |-- UserDialog.tsx
|   |   |   |   |-- UsersPage.test.tsx
|   |   |   |   |-- UsersPage.tsx
|   |   |   |   `-- UsersSummary.tsx
|   |   |   `-- AGENTS.md
|   |   |-- lib/
|   |   |   |-- api.ts
|   |   |   |-- navigation.test.ts
|   |   |   |-- navigation.ts
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
|-- .env.test.example
|-- .gitignore
|-- AGENTS.md
|-- docker-compose.yml
|-- package.json
|-- pnpm-lock.yaml
`-- README.md
```

## Tanggung jawab dan batas lapisan

| Lokasi | Tanggung jawab | Batas |
| --- | --- | --- |
| `backend/app/main.py` | Merangkai FastAPI, middleware, lifespan, dan router | Aturan penilaian dan persistence berada pada lapisan di bawahnya. |
| `backend/app/config.py` | Settings Pydantic dengan cache | Pusatkan pembacaan environment agar default tidak tersebar. |
| `backend/app/database.py` | Async engine, session factory, dan request dependency | Session request tidak melakukan commit otomatis. |
| `backend/app/dependencies.py` | Identitas JWT, akun aktif, dan dependency role | Service memeriksa kepemilikan resource. |
| `backend/app/routers/` | Adapter HTTP dan status code | Delegasikan aturan bisnis serta query. |
| `backend/app/schemas/` | Kontrak request/response dan constraint field | Validasi lintas-record/database berada pada service. |
| `backend/app/services/` | Aturan akses, perhitungan nilai, rilis, laporan, dan transport email | Periksa perilaku commit repository saat menyusun transaksi. |
| `backend/app/repositories/` | Query dan persistence SQLAlchemy | Hindari duplikasi aturan bisnis antar-repository. |
| `backend/app/models/` | Tabel, foreign key, constraint, dan komentar metadata Indonesia | Perubahan schema memerlukan migration Alembic. |
| `backend/app/seeding/` | Generator graph opsional, katalog sample, transaksi dataset append-only, CLI, dan artefak manifest | Pertahankan dataset manual; gunakan nama baru untuk initial state yang segar. |
| `backend/app/tasks/` dan `celery_app.py` | Task pengiriman Celery melalui Redis | Gunakan service notifikasi, bukan HTTP handler. |
| `backend/app/templates/` | Layout PDF Jinja2 | Pertahankan larangan pengambilan resource eksternal. |
| `backend/alembic/versions/` | Migration database bertahap | Pertahankan revision yang sudah diterapkan beserta komentar metadata. |
| `backend/scripts/verify_comments.py` | Pemeriksaan komentar tabel/kolom PostgreSQL | Memeriksa metadata database, bukan komentar Python. |
| `backend/tests/` | Test API, persistence, concurrency, seed, laporan, dan email | Gunakan PostgreSQL disposable yang dimigrasi/di-seed dengan target `TEST_*` eksplisit. |
| `backend/tests/support/` | Guard target awal dan fixture dataset API hasil generator | Konfigurasikan target test sebelum import runtime aplikasi. |
| `frontend/src/App.tsx`, `main.tsx` | Provider, routing, dan mounting | UI khusus fitur berada dalam folder features. |
| `frontend/src/features/academic/` | Kontrak/hook API akademik serta UI pengelolaan bersama | Logic sesi HTTP tetap dalam client bersama. |
| `frontend/src/features/grades/` | State draft nilai, grid, koordinasi rilis, dan navigation guard | Pertahankan edit yang tertunda saat berpindah tab kelas. |
| `frontend/src/features/users/` | Daftar, ringkasan, dialog create/edit/deactivation, dan kontrak akun | Password tidak menjadi field respons publik atau record yang dirender. |
| Folder lain `frontend/src/features/` | Auth, courses, classes, students, components, dashboard, analytics, reports, notifications | Dekatkan logic fitur dengan halamannya. |
| `frontend/src/components/` | Layout, navigasi, route guard, dan komponen bersama | Alur bisnis tetap berada pada folder fitur. |
| `frontend/src/components/data-table/` | Sorting, pagination, toolbar, dan empty state TanStack Table bersama | Halaman fitur memiliki request API dan filter server. |
| `frontend/src/components/ui/` | Primitive shadcn/Base UI | Hindari perilaku domain pada primitive. |
| `frontend/src/lib/` | Client Axios bersama, helper navigasi, dan utilitas styling | Gunakan client ini agar bearer/refresh konsisten. |
| `frontend/src/stores/` | Persistence/hydration sesi Zustand | Data query server memakai TanStack Query. |
| `frontend/src/test/` | Setup DOM Vitest bersama | Test fitur lainnya berada di samping fitur terkait. |
| `frontend/public/`, `frontend/src/assets/` | Aset statis publik dan aset import | Bundle production dihasilkan pada `dist/` yang diabaikan Git. |
| `nginx/`, konfigurasi Nginx frontend | Edge API proxy dan fallback SPA statis | Terminasi TLS berada di luar proxy repository. |
| `docker-compose.yml`, Dockerfile | Topologi dan image local/deployment | Gunakan file, port, dan project name sesuai profile. |
| `backend/.artifacts/seeding/` (diabaikan Git, hasil generator) | Manifest CLI saat dijalankan dari `backend/` atau container backend lokal | Pertahankan artefak dataset; jangan simpan password atau token. |
| `.env*.example` | Template konfigurasi | Jangan commit secret atau file environment aktual. |
| `docs/superpowers/specs/` | Arsip specification desain | Cocokkan perilaku usulan dengan source saat ini. |
| `docs/superpowers/plans/` | Arsip plan/progres implementasi | Command historis dapat berbeda dari panduan aktif. |

## Titik awal penelusuran

Untuk alur request, telusuri router ke schema/service, lalu repository/model. Untuk konsistensi nilai, mulai dari `services/grade.py`, `services/scores.py`, serta `services/component_rules.py`. Untuk state editor, mulai dari `features/grades/draft.ts` dan `hooks.ts`. Untuk operasi, gunakan [instalasi](installation.md), [pengujian](testing.md), dan [deployment](deployment.md).
