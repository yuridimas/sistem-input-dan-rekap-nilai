# Sistem Input & Rekap Nilai

Aplikasi pengelolaan nilai akademik untuk dosen dan superadmin. Backend menggunakan FastAPI, SQLAlchemy, PostgreSQL, Celery, dan Redis; frontend berupa React, TypeScript, dan Vite.

## Fitur

- Input nilai per komponen dan kalkulasi nilai akhir berbobot.
- Dashboard, grafik performa, riwayat semester, ranking, serta pengelolaan banyak mata kuliah dan kelas.
- Finalisasi nilai dan notifikasi email asinkron.
- Ekspor rekap PDF dan Excel.

## Prasyarat

- Docker Compose untuk menjalankan stack lengkap.
- Untuk development tanpa Docker: Python 3.11+, Node sesuai versi di `frontend/package.json`, PostgreSQL 18, dan Redis.

## Setup lokal dengan Docker

Salin `.env.example` menjadi `.env.local`, lalu ganti `JWT_SECRET` dan `SUPERADMIN_PASSWORD`. Untuk perintah Compose di bawah, ubah host `DATABASE_URL` menjadi `db` dan host `REDIS_URL` menjadi `redis` (contoh: `postgresql+asyncpg://postgres:postgres@db:5432/grades` dan `redis://redis:6379/0`). Template `.env.example` memakai `localhost`, yang sesuai bila backend dijalankan langsung di host; pada mode tersebut biarkan host URL tetap `localhost`.

```powershell
Copy-Item .env.example .env.local
docker compose --env-file .env.local --profile local up -d db redis
docker compose --env-file .env.local --profile local run --rm backend alembic upgrade head
docker compose --env-file .env.local --profile local up --build -d
```

Buka frontend di <http://localhost:5173> dan API di <http://localhost:8000>. API health tersedia di `/health`. Saat backend pertama kali mulai, aplikasi membuat superadmin dari `SUPERADMIN_EMAIL`, `SUPERADMIN_PASSWORD`, dan `SUPERADMIN_NAME` jika email tersebut belum ada. Proses ini idempoten; proses ini tidak mengganti kata sandi akun yang sudah ada.

Untuk development tanpa Docker, jalankan PostgreSQL dan Redis, siapkan `backend/.env` dengan URL yang sesuai, lalu dari `backend/` jalankan:

```sh
python -m pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

Di terminal lain, dari `frontend/`, jalankan `npm ci` lalu `npm run dev`. Jika frontend dijalankan langsung di host, atur `VITE_API_URL=http://localhost:8000` pada environment proses Vite atau `frontend/.env.local`.

## Staging dan production

Salin `.env.staging.example` atau `.env.prod.example` ke `.env.staging` atau `.env.prod`; isi secret unik, kredensial SMTP, dan origin HTTPS yang benar. File env aktual diabaikan Git. Gunakan nama project Compose yang berbeda agar database, network, dan layanan kedua lingkungan terpisah.

```sh
docker compose -p nilai-staging --env-file .env.staging --profile staging up --build --wait
docker compose -p nilai-prod --env-file .env.prod --profile prod up --build --wait
```

Profil deployment menjalankan migrasi sebelum API dan worker, menyajikan frontend statis melalui Nginx, dan mengikat port edge ke loopback. Terminasi TLS dilakukan reverse proxy eksternal pada host. Sesuaikan port dan konfigurasi proxy dengan environment masing-masing.

## Konfigurasi

| Variabel | Kegunaan |
| --- | --- |
| `DATABASE_URL`, `REDIS_URL` | Koneksi backend; host Compose adalah `db`/`redis` untuk lokal dan `db-deploy`/`redis` untuk deployment. |
| `JWT_SECRET` | Kunci penandatanganan token; wajib diganti di luar development lokal. |
| `SUPERADMIN_EMAIL`, `SUPERADMIN_PASSWORD`, `SUPERADMIN_NAME` | Bootstrap akun administrator pertama. |
| `CORS_ORIGINS`, `INSTITUTION_NAME` | Origin frontend yang diizinkan dan nama institusi pada laporan. |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_SECURITY` | Pengiriman email; konfigurasi SMTP kosong cocok untuk development/mock. |
| `VITE_API_URL` | URL API frontend; default lokal `http://localhost:8000`, deployment `/api`. |

Mulai dari `.env.example` untuk lokal dan template environment terkait untuk deployment. Jangan commit secret atau file `.env.*` aktual.

## Migrasi, pemeriksaan, dan test

Jalankan dari `backend/` setelah database tersedia dan termigrasi:

```sh
alembic upgrade head
python scripts/verify_comments.py
python -m pytest
```

`verify_comments.py` memeriksa komentar tabel dan kolom aplikasi pada schema PostgreSQL `public`. Jalankan test backend hanya pada database disposable yang sesuai konfigurasi test.

Jalankan dari `frontend/`:

```sh
npm ci
npm test
npm run build
npm run lint
```

## English setup summary

Copy `.env.example` to `.env.local`, replace the local JWT and admin password, and set the database/Redis URL hosts to `db`/`redis` for Compose. Keep `localhost` when running the backend directly on the host. Apply Alembic migrations before starting the full local profile. The first backend startup idempotently creates the configured superadmin when that email does not exist. For staging or production, copy the matching example env file, replace every placeholder, use a distinct Compose project name, and terminate HTTPS at the external host reverse proxy. Backend checks and tests require a migrated disposable PostgreSQL database; frontend checks run with the commands above.
