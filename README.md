# Sistem Input & Rekap Nilai

## Dokumentasi

| Panduan | Isi |
| --- | --- |
| [Arsitektur](docs/architecture.md) | Komponen runtime, relasi data, state, dan alur rilis |
| [Struktur repository](docs/structure.md) | Susunan file, layer, dan batas tanggung jawab |
| [Instalasi](docs/installation.md) | Docker, development di host, pemilihan environment, dan port |
| [Keputusan teknis](docs/decisions.md) | Pilihan implementasi beserta trade-off |
| [Panduan penggunaan](docs/usage.md) | Pengelolaan akun, mata kuliah/kelas, nilai, dan laporan |
| [Referensi API](docs/api.md) | Operasi HTTP, payload, respons, error, dan seed CLI |
| [Pengujian](docs/testing.md) | Database disposable dan pemeriksaan frontend |
| [Data dummy persisten](docs/seeding.md) | Dataset berulang untuk uji manual dan load ringan |
| [Deployment](docs/deployment.md) | Profile staging/production, proxy, TLS, dan pemeriksaan operasional |

## Deskripsi

Aplikasi FastAPI dan React untuk mengelola komponen penilaian, input nilai, rilis nilai kelas, ranking, laporan, serta notifikasi rilis. Dosen bekerja pada kelas yang ditugaskan kepadanya; superadmin mengelola akun dan dapat mengakses seluruh kelas. Profil mahasiswa merupakan data akademik dan penerima email, terpisah dari akun login.

Alur utamanya adalah menyiapkan mata kuliah/kelas, mengisi roster dan bobot penilaian, menyimpan skor draft, lalu memfinalisasi nilai agar tersedia pada ranking, history, dan laporan PDF/XLSX.

## Quick start

Prasyarat: Git, Docker dengan Linux containers, dan Docker Compose v2. Semua perintah berikut dijalankan dari **root repository menggunakan PowerShell**.

1. Salin template environment lokal:

   ```powershell
   Copy-Item .env.example .env.local
   ```

2. Edit `.env.local`: ganti `JWT_SECRET` dan `SUPERADMIN_PASSWORD`, lalu gunakan nama layanan untuk koneksi antar-container:

   ```dotenv
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/grades
   REDIS_URL=redis://redis:6379/0
   ```

   Ini adalah default database lokal. Jika diubah, samakan `POSTGRES_USER`, `POSTGRES_PASSWORD`, dan `POSTGRES_DB` dengan `DATABASE_URL`.

3. Validasi Compose, jalankan dependensi, terapkan migration, lalu mulai seluruh stack:

   ```powershell
   docker compose --env-file .env.local --profile local config --quiet
   docker compose --env-file .env.local --profile local up -d --wait db redis
   docker compose --env-file .env.local --profile local run --build --rm backend alembic upgrade head
   docker compose --env-file .env.local --profile local up -d --build --wait
   Invoke-RestMethod http://localhost:18000/health
   ```

Pastikan `db` dan `redis` bernilai `true`; `status: ok` saja belum membuktikan dependensi siap.

| Layanan | URL lokal |
| --- | --- |
| Frontend | <http://localhost:15173> |
| API | <http://localhost:18000> |
| Swagger UI | <http://localhost:18000/docs> |

Login menggunakan `SUPERADMIN_EMAIL` dan `SUPERADMIN_PASSWORD` dari `.env.local`. Startup hanya membuat akun jika email belum terdaftar; perubahan environment tidak mereset password akun yang sudah ada. Untuk mata kuliah/kelas berisi data serta beberapa contoh per kasus positif/negatif, ikuti [panduan seeding](docs/seeding.md).

## Teknologi yang digunakan

| Bagian | Stack |
| --- | --- |
| API dan persistence | Python 3.11+, FastAPI, Pydantic, SQLAlchemy async/asyncpg, Alembic, PostgreSQL 18 |
| Pengiriman background | Celery, Redis 7, SMTP/mock transport yang dapat dikonfigurasi |
| Aplikasi browser | React, TypeScript, Vite, React Router, TanStack Query/Table, Axios, Zustand |
| UI dan chart | Tailwind CSS, shadcn/Base UI, Recharts |
| Laporan dan seed data | Jinja2, WeasyPrint, openpyxl, Polyfactory/Faker opsional |
| Pemeriksaan | pytest/pytest-asyncio/HTTPX, Vitest/React Testing Library, TypeScript, Oxlint |

## Instalasi singkat

Siapkan file environment, jalankan migration pada database tujuan, lalu mulai stack seperti langkah quick start. Development langsung di host memerlukan Python 3.11+ serta Node.js yang memenuhi [manifest frontend](frontend/package.json). [Panduan instalasi](docs/installation.md) menjelaskan virtual environment, URL host, dan dependensi native PDF.

## Ringkasan arsitektur

Router FastAPI mengikat kontrak request, service menegakkan otorisasi dan aturan penilaian, sedangkan repository menyimpan record PostgreSQL. React mengelola data server melalui TanStack Query dan menyimpan edit nilai yang belum terkirim dalam draft engine tersendiri. Finalisasi melakukan commit nilai, ranking, dan audit notifikasi sebelum memublikasikan task Celery. Deployment melayani aset statis dan meneruskan `/api` melalui Nginx; infrastruktur eksternal menangani terminasi TLS. Lihat [arsitektur](docs/architecture.md).

## Struktur proyek

```text
backend/       API, service, repository, model, seeding, migration, dan test
frontend/      Fitur React, UI/tabel bersama, state, dan test browser
docs/          Panduan aktif dan arsip plan/specification Superpowers
nginx/         Konfigurasi edge proxy deployment
docker-compose.yml
```

Lihat [struktur lengkap](docs/structure.md), [panduan backend](backend/README.md), [panduan frontend](frontend/README.md), dan [AGENTS.md](AGENTS.md) untuk konvensi kontribusi. Jalankan perintah npm dari `frontend/`; root `package.json` bukan runner frontend.

## Port Docker pada host

| Layanan | Port internal container | Lokal | Staging | Production |
| --- | --- | --- | --- | --- |
| PostgreSQL | 5432 | 15432 | 25432 | 35432 |
| Redis | 6379 | 16379 | 26379 | 36379 |
| API lokal | 8000 | 18000 | Melalui proxy | Melalui proxy |
| Vite lokal | 5173 | 15173 | Aset statis | Aset statis |
| Nginx deployment | 80 | Tidak diaktifkan | 28080 | 38080 |

Ubah `DB_HOST_PORT`, `REDIS_HOST_PORT`, `BACKEND_HOST_PORT`, `FRONTEND_HOST_PORT`, atau `HTTP_PORT` untuk memilih port host lain. Template lokal menurunkan `VITE_API_URL` dan `CORS_ORIGINS` dari nilai tersebut; sesuaikan juga URL/origin yang diisi eksplisit. Koneksi antar-container tetap menggunakan port internal, seperti `db:5432` dan `redis:6379`. Worker dan migration tidak memublikasikan port.

## Pemilihan environment

| Runtime | File | Host koneksi |
| --- | --- | --- |
| API/worker Compose lokal | `.env.local` di root | PostgreSQL `db`, Redis `redis` |
| API di host, working directory `backend/` | `backend/.env` atau environment proses | `localhost` dan port host Docker |
| Vite di host | `frontend/.env.local` | API Docker: `http://localhost:18000`; API native: `http://localhost:8000` |
| Staging/production | `.env.staging` / `.env.prod` melalui `APP_ENV_FILE` | PostgreSQL `db-deploy`, Redis `redis` |

Compose `--env-file` memasok nilai interpolasi; `env_file` pada layanan memasok environment container. Layanan lokal tetap memilih `.env.local`. Backend di host membaca `.env` relatif terhadap working directory dan mengutamakan environment proses. Jangan commit file environment aktual atau secret.

Isi `INSTITUTION_NAME` untuk identitas institusi pada laporan. `SMTP_HOST` kosong memilih mock email transport; lihat [konfigurasi email dan worker](backend/README.md#email-dan-worker).

## Perintah harian

```powershell
docker compose --env-file .env.local --profile local ps
docker compose --env-file .env.local --profile local logs -f backend worker
docker compose --env-file .env.local --profile local exec backend alembic current
docker compose --env-file .env.local --profile local exec backend python scripts/verify_comments.py
docker compose --env-file .env.local --profile local down
```

`down` menghentikan stack dan mempertahankan named volume database. Jalankan `up` kembali untuk memulainya. Pytest hanya boleh menggunakan target disposable yang dipilih eksplisit dalam [panduan pengujian](docs/testing.md). Arsip `docs/superpowers/` merekam usulan terdahulu; gunakan panduan aktif dan konfigurasi saat ini untuk operasi.
