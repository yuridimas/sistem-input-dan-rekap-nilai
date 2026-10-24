# Sistem Input & Rekap Nilai — Design Spec

**Date:** 2026-10-24
**Status:** Draft (pending user review)
**Approach:** Modular Monolith (FastAPI + React)
**Purpose:** Portfolio project — a lecturer-facing grade input and recap system.

---

## 1. Overview

A web application for lecturers (dosen) to input, compute, recap, and release student grades across multiple courses and class sections. Students have no login; they receive their grades via email when a lecturer releases them. A superadmin manages lecturer accounts and global data.

### 1.1 Users & Roles

- **Superadmin** — manages lecturers, courses, classes, global config; views all data.
- **Lecturer (Dosen)** — manages own courses/classes, rosters, components, scores, finalization, exports, notifications.
- **Student (Mahasiswa)** — no account; identified by NIM + email; receives grade-release emails.

### 1.2 Ten Core Features

1. Input nilai mahasiswa (per-component score entry)
2. Perhitungan nilai otomatis (weighted final score)
3. Grafik performa mahasiswa (trend, distribution, component breakdown)
4. Export nilai (PDF + Excel, per-student and per-class)
5. Dashboard dosen (cross-course summary with drill-down)
6. Kategori komponen nilai (tugas, UTS, UAS, custom weights; UTS+UAS required; weights sum to 100%)
7. Riwayat nilai per semester (immutable after release)
8. Notifikasi ke mahasiswa saat nilai rilis (email, async)
9. Ranking / peringkat kelas (sequential, course-level available)
10. Multi-mata kuliah / multi-kelas dalam satu dashboard

---

## 2. Tech Stack (latest major; verify installed versions before execution)

- **Backend:** FastAPI (latest major), Python 3.11+, SQLAlchemy 2.0 (async), Alembic, Pydantic v2, Celery + Redis, WeasyPrint (PDF), openpyxl (Excel), bcrypt, python-jose (JWT).
- **Frontend:** React 18/19 (latest major), Vite, TypeScript, Tailwind CSS + shadcn/ui, Recharts, React Router, TanStack Query, Zustand.
- **Database:** PostgreSQL 18 (matches local install).
- **Infra:** Docker Compose with `local` / `staging` / `prod` profiles; nginx reverse proxy; env-based config (pydantic-settings).

Version verification is a prerequisite of the implementation plan (check `python --version`, `node --version`, `psql --version`, etc. and pin exact majors).

---

## 3. Architecture

Modular monolith: a single FastAPI application organized into domain modules, each with `router.py`, `service.py`, `repository.py`, `schemas.py`, `models.py`. Single deployable backend container + single frontend container.

### 3.1 Backend Modules

1. `auth` — login, JWT issue/refresh, password hashing, role guards.
2. `users` — lecturer CRUD (superadmin), profile.
3. `courses` — course CRUD.
4. `classes` — class sections per course, lecturer assignment, roster.
5. `students` — student records (no auth).
6. `components` — grade components per class.
7. `grades` — scores + final computed grade, draft/finalized status, release.
8. `ranking` — compute/store rankings.
9. `notifications` — Celery email tasks + delivery audit.
10. `reports` — PDF + Excel export.

### 3.2 Frontend Feature Folders

Mirror backend modules under `src/features/`: `auth`, `dashboard`, `courses`, `classes`, `students`, `components`, `grades`, `ranking`, `reports`, `notifications`. Shared `ui/` (shadcn), `lib/` (api client, auth store).

### 3.3 Cross-Cutting

Dependency-injected async DB session, role-based access dependency, global error handler returning `{detail, code}`, structured logging, CORS allowlist per env.

---

## 4. Data Model

All tables and columns MUST carry a Bahasa Indonesia `COMMENT` (via SQLAlchemy `comment=` and Alembic `COMMENT ON`). Names in English (code), comments in Bahasa Indonesia.

### 4.1 Tables

**users**
- `id` uuid PK — "Identitas unik pengguna"
- `email` varchar(255) unique not null — "Alamat email pengguna (untuk login)"
- `password_hash` varchar(255) not null — "Hash kata sandi (bcrypt)"
- `full_name` varchar(255) not null — "Nama lengkap pengguna"
- `role` varchar(20) not null — "Peran: superadmin atau dosen"
- `is_active` boolean default true — "Status aktif pengguna"
- `created_at` timestamptz — "Waktu pembuatan akun"
- `updated_at` timestamptz — "Waktu pembaruan terakhir"

**courses**
- `id` uuid PK
- `code` varchar(50) unique not null — "Kode mata kuliah"
- `name` varchar(255) not null — "Nama mata kuliah"
- `credits` int not null — "Jumlah SKS"
- `semester` varchar(20) not null — "Semester (mis. 2026/1)"
- `created_by` uuid FK users — "Pengguna yang membuat"
- `created_at` timestamptz

**classes**
- `id` uuid PK
- `course_id` uuid FK courses not null
- `section` varchar(10) not null — "Kelas/seksi (mis. A, B)"
- `lecturer_id` uuid FK users not null — "Dosen pengampu"
- `academic_year` varchar(20) not null — "Tahun akademik"
- `created_at` timestamptz
- Unique `(course_id, section, academic_year)`

**students**
- `id` uuid PK
- `nim` varchar(50) unique not null — "Nomor Induk Mahasiswa"
- `full_name` varchar(255) not null — "Nama lengkap mahasiswa"
- `email` varchar(255) not null — "Email mahasiswa (untuk notifikasi)"
- `created_at` timestamptz

**enrollments**
- `id` uuid PK
- `class_id` uuid FK classes not null
- `student_id` uuid FK students not null
- `enrolled_at` timestamptz
- Unique `(class_id, student_id)`

**components**
- `id` uuid PK
- `class_id` uuid FK classes not null
- `name` varchar(100) not null — "Nama komponen (mis. Tugas 1, UTS)"
- `category` varchar(20) not null — "Kategori: tugas, uts, uas, custom"
- `weight` numeric(5,2) not null — "Bobot dalam persen"
- `max_score` numeric(6,2) default 100 — "Nilai maksimum komponen"
- `order_index` int default 0 — "Urutan tampilan"
- `created_at` timestamptz
- Constraints: per class sum(weight)=100; at least one UTS and one UAS; weight>0.

**scores**
- `id` uuid PK
- `enrollment_id` uuid FK enrollments not null
- `component_id` uuid FK components not null
- `score` numeric(6,2) not null — "Nilai yang diperoleh"
- `entered_by` uuid FK users not null
- `entered_at` timestamptz
- `updated_at` timestamptz
- Unique `(enrollment_id, component_id)`

**grades**
- `id` uuid PK
- `enrollment_id` uuid FK enrollments unique not null
- `final_score` numeric(6,2) not null — "Nilai akhir (terbobot)"
- `status` varchar(20) not null — "Status: draft atau finalized"
- `finalized_at` timestamptz — "Waktu finalisasi"
- `finalized_by` uuid FK users
- `release_notified_at` timestamptz — "Waktu notifikasi rilis terkirim"

**rankings**
- `id` uuid PK
- `class_id` uuid FK classes not null
- `enrollment_id` uuid FK enrollments not null
- `rank` int not null — "Peringkat (berurutan)"
- `computed_at` timestamptz

**notifications**
- `id` uuid PK
- `grade_id` uuid FK grades not null
- `student_email` varchar(255) not null
- `status` varchar(20) not null — "queued/sent/failed"
- `error_message` text
- `sent_at` timestamptz
- `created_at` timestamptz

**audit_log** (superadmin actions)
- `id` uuid PK
- `actor_id` uuid FK users
- `action` varchar(100) not null
- `target_type` varchar(50)
- `target_id` uuid
- `payload` jsonb
- `created_at` timestamptz

### 4.2 Indexes

FKs indexed; `(class_id, student)` for roster; `(enrollment_id)` for grade; `(status)` on grades; `(class_id)` on rankings.

---

## 5. Key Workflows

### 5.1 Grade Entry
1. Lecturer selects class → roster × components grid.
2. Enter scores (0 ≤ score ≤ max_score). Frontend + backend validation.
3. Saved as `draft` (upsert). Final score auto-recomputed (weighted sum).
4. "Finalisasi & Rilis" → backend verifies all components scored for all enrollments → set `finalized`, compute sequential ranking → enqueue Celery email per student → return 202.

### 5.2 Notification (Celery)
Task `send_grade_release_email` async. Pluggable mailer: dev → log + mark sent (mock); prod → SMTP (env). Retries 3× with backoff; failure → `notifications.status=failed`. Superadmin can view/retry failed.

### 5.3 Dashboard
`GET /dashboard/summary` → courses taught, class count, pending (draft) classes, recently released. Drill-down: course → classes → roster → student detail (scores, final, rank, trend).

### 5.4 Export
- `GET /reports/student/{enrollment_id}/pdf` → WeasyPrint renders HTML template (institution header, student info, component table, final, rank, pass/fail) → PDF stream.
- `GET /reports/class/{class_id}/xlsx` → openpyxl roster with all component scores + final + rank → xlsx stream.
- Both streamed with `Content-Disposition`.

### 5.5 Charts (Recharts, frontend)
- Student trend: line chart of final scores across semesters.
- Class distribution: bar/histogram of final score buckets.
- Component breakdown: stacked bar (tugas/UTS/UAS/custom) per student or class average.

### 5.6 Ranking
Recomputed on finalization. Sequential: sort final desc → assign 1..N (ties broken by NIM then name). Stored in `rankings`. Available per class and per course.

### 5.7 Auth
`POST /auth/login` → JWT access (15 min) + refresh (7 d). Role-guard dependency on routes. Superadmin endpoints under `/admin/*`.

---

## 6. Validation, Errors & Security

- Score range `0 ≤ score ≤ max_score`.
- Weights sum to 100 per class; ≥1 UTS + ≥1 UAS; weight > 0.
- Finalize blocked if any enrollment missing a score → `422` with missing list.
- Duplicate NIM/email → `409`. Role violation → `403`.
- Global error handler → `{detail, code}` + status. Celery failures logged, never crash request.
- Passwords bcrypt (cost 12). JWT access 15min / refresh 7d rotated. Login rate-limited (slowapi). CORS allowlist per env. ORM only (no raw concat). Secrets via env.

---

## 7. Testing

- Backend: pytest + pytest-asyncio + httpx. Unit tests for services (grade calc, ranking, weight validation). Integration tests against test Postgres. Coverage ≥ 80% on services.
- Frontend: Vitest + RTL for components; Playwright for E2E (login → enter grades → finalize → export).
- No CI pipeline (manual runs).

---

## 8. Deployment & Docker

Compose profiles `local`/`staging`/`prod` with env files (`.env.local`, `.env.staging`, `.env.prod`).

- `local`: Postgres 18 + Redis + backend (hot reload) + frontend (Vite dev).
- `staging`/`prod`: Postgres + Redis + backend (uvicorn workers) + frontend (built, served by nginx) + nginx reverse proxy.
- Migrations: Alembic `upgrade head` on backend startup (locked). Seed creates superadmin from env on first run.
- Healthcheck: `/health` (DB + Redis ping).
- Backups: documented `pg_dump` script for prod.

---

## 9. Out of Scope

- Student login/portal.
- Letter grades (pure numeric; fail if < 45).
- Editing finalized grades (immutable).
- GitHub Actions CI.
- Multi-tenant across institutions (single institution; data scoped by lecturer/admin).

---

## 10. Open Decisions (to resolve in planning)

- Exact pinned major versions after local verification.
- Institution name/logo for PDF header (configurable via env; falls back to text-only header when unset).
- Ranking tie-break final rule (NIM then name) — confirm.
- Email provider for prod (SMTP env-configurable; dev uses mock logger).
