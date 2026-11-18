# Instalasi

## Prasyarat

- Git, Docker dengan Linux containers, dan Docker Compose v2 untuk menjalankan seluruh stack.
- Untuk development di host: Python 3.11+ dan Node.js yang memenuhi `^22.22.2 || ^24.15.0 || >=26.0.0`, sesuai [`package.json`](../frontend/package.json).
- PostgreSQL dan Redis, yang disediakan Compose pada langkah berikut.

Perintah menggunakan **PowerShell** kecuali ditandai sebagai perintah shell container. Clone memakai URL repository milikmu:

```powershell
$repositoryUrl = Read-Host 'URL clone repository'
git clone $repositoryUrl sistem-input-dan-rekap-nilai
Set-Location sistem-input-dan-rekap-nilai
```

Untuk checkout yang sudah ada, mulai dari root repository.

## Stack lokal lengkap

Dari **root repository**:

```powershell
Copy-Item .env.example .env.local
```

Edit `.env.local`: ganti `JWT_SECRET` dan `SUPERADMIN_PASSWORD`, lalu gunakan alamat container:

```dotenv
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/grades
REDIS_URL=redis://redis:6379/0
```

Template awal memakai alamat host sehingga perlu disesuaikan untuk API/worker container. Default Compose lokal membuat user `postgres`, password `postgres`, dan database `grades`. Jika diubah, isi `POSTGRES_USER`, `POSTGRES_PASSWORD`, dan `POSTGRES_DB` yang cocok dengan `DATABASE_URL`. Gunakan credential URL-safe atau percent-encoding pada password di URL.

```powershell
docker compose --env-file .env.local --profile local config --quiet
docker compose --env-file .env.local --profile local up -d --wait db redis
docker compose --env-file .env.local --profile local run --build --rm backend alembic upgrade head
docker compose --env-file .env.local --profile local up -d --build --wait
docker compose --env-file .env.local --profile local ps
Invoke-RestMethod http://localhost:18000/health
```

Startup lokal memerlukan migration eksplisit. Pastikan kedua flag dependensi bernilai `true`, buka <http://localhost:15173>, lalu login dengan superadmin yang dikonfigurasi. Swagger UI langsung tersedia di <http://localhost:18000/docs>.

Bootstrap seed hanya menambah akun jika email belum ada serta email/password tidak kosong. Perubahan environment tidak mereset password yang sudah tersimpan. Startup menelan error seed; jalankan perintah berikut untuk melihat kegagalan secara eksplisit:

```powershell
docker compose --env-file .env.local --profile local exec backend python -c "import asyncio; from app.services.seed import seed_superadmin; asyncio.run(seed_superadmin())"
```

## Pemilihan environment

| Proses | File | Alamat database / Redis |
| --- | --- | --- |
| API/worker Compose lokal | `.env.local` di root | `db:5432`, `redis:6379` |
| API di host, working directory `backend/` | `backend/.env` atau environment proses | `localhost:15432`, `localhost:16379` pada mapping Docker default |
| Vite di host | `frontend/.env.local` | URL API yang dapat diakses browser |
| Staging/production | `.env.staging` / `.env.prod` dipilih melalui `APP_ENV_FILE` | `db-deploy:5432`, `redis:6379` |

Compose `--env-file` memasok nilai interpolasi; `env_file` pada layanan memasok environment container. API/worker lokal secara eksplisit membaca `.env.local`. Deployment memilih file melalui `APP_ENV_FILE`. Environment shell dapat menimpa interpolasi Compose.

Pydantic membaca `.env` relatif terhadap working directory dan mengutamakan environment proses. Settings dicache per proses; restart setelah mengedit konfigurasi. Vite memerlukan restart saat development atau rebuild untuk deployment. Jangan commit file environment aktual.

| Setting | Fungsi / default |
| --- | --- |
| `DATABASE_URL` | URL PostgreSQL menggunakan `postgresql+asyncpg` |
| `REDIS_URL` | Broker Celery dan health probe Redis |
| `JWT_SECRET`, `JWT_ALGORITHM` | Penandatanganan token; algoritma default `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS` | Default 15 menit / tujuh hari |
| `SUPERADMIN_EMAIL`, `SUPERADMIN_PASSWORD`, `SUPERADMIN_NAME` | Akun bootstrap idempotent |
| `CORS_ORIGINS` | Array JSON origin browser, termasuk scheme/port |
| `APP_NAME`, `DEBUG` | Judul API dan debug/SQL logging |
| `INSTITUTION_NAME` | Nama institusi pada laporan |
| `SMTP_HOST` | Nilai kosong memilih mock transport |
| `SMTP_PORT`, `SMTP_SECURITY` | Default 587 / `starttls`; mendukung `ssl` dan `none` |
| `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | Credential SMTP dan alamat pengirim |
| `SMTP_TIMEOUT` | Default 10 detik; lebih besar dari nol dan maksimal 60 |
| `VITE_API_URL` | Base URL API untuk browser; fallback client `http://localhost:8000` |
| `DB_HOST_PORT`, `REDIS_HOST_PORT`, `BACKEND_HOST_PORT`, `FRONTEND_HOST_PORT` | Override port host lokal |
| `APP_ENV_FILE`, `DEPLOYMENT_ENV`, `HTTP_PORT`, `UVICORN_WORKERS` | Pemilihan deployment, port proxy, dan jumlah proses |
| `APP_ENV`, `SEED_PASSWORD` | Seed CLI: environment local/development eksplisit dan password akun demo baru |
| `TEST_DATABASE_URL`, `TEST_REDIS_URL`, `TEST_DATABASE_DISPOSABLE` | Target disposable eksplisit yang diwajibkan pytest; lihat [pengujian](testing.md) |

Nilai `VITE_*` menjadi konten publik di bundle. Mock transport dapat menandai notifikasi `sent` tanpa menghubungi SMTP.

## Port

| Layanan | Internal | Lokal | Staging | Production |
| --- | --- | --- | --- | --- |
| PostgreSQL | 5432 | 15432 | 25432 | 35432 |
| Redis | 6379 | 16379 | 26379 | 36379 |
| API lokal | 8000 | 18000 | Melalui proxy | Melalui proxy |
| Vite lokal | 5173 | 15173 | Aset statis | Aset statis |
| Edge proxy | 80 | Tidak diaktifkan | 28080 | 38080 |

Database, Redis, dan proxy deployment bind ke loopback. URL antar-container memakai nama layanan dan port internal. Sesuaikan `VITE_API_URL`/`CORS_ORIGINS` yang diisi eksplisit saat mengubah port host. Vite/Uvicorn native memakai default 5173/8000 sehingga dapat berjalan bersama mapping Docker.

## Backend di host

Dari **root repository**:

```powershell
docker compose --env-file .env.local --profile local up -d --wait db redis
python -m venv backend/.venv
Copy-Item .env.example backend/.env
```

Edit `backend/.env` dengan URL host: `postgresql+asyncpg://postgres:postgres@localhost:15432/grades` dan `redis://localhost:16379/0` untuk mapping Docker default. Ganti secret dan credential bootstrap. Kemudian jalankan:

```powershell
Set-Location backend
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,seed]"
alembic upgrade head
uvicorn app.main:app --reload
```

Aktivasi POSIX memakai `source .venv/bin/activate`. Buka <http://localhost:8000/docs>. PDF memerlukan Pango, HarfBuzz, dan font yang disediakan [Dockerfile backend](../backend/Dockerfile); gunakan Docker untuk rendering di Windows.

Jalankan worker dengan database/Redis yang sama. Dari **PowerShell lain pada root repository**:

```powershell
docker compose --env-file .env.local --profile local up -d --build worker
```

Untuk host Linux/WSL yang sudah memiliki dependensi, jalankan `celery -A app.celery_app:celery_app worker --loglevel=info` dari **`backend/`** pada shell lain dengan virtual environment aktif. Lihat [panduan backend](../backend/README.md#email-dan-worker).

## Frontend di host

Dari **root repository**:

```powershell
Set-Location frontend
npm ci
```

Buat `frontend/.env.local`:

```dotenv
VITE_API_URL=http://localhost:18000
```

Gunakan `http://localhost:8000` untuk API native. Dari **`frontend/`**:

```powershell
npm run dev
```

Buka <http://localhost:5173>. Izinkan origin tersebut pada `CORS_ORIGINS` backend. Lihat [development frontend](../frontend/README.md).

## Dataset dummy opsional

Extra `seed` memasang Polyfactory dan Faker. Instalasi host di atas sudah menyertakannya; image runtime backend hanya memasang package dasar. Siapkan container lokal yang sedang berjalan dengan:

```powershell
docker compose --env-file .env.local --profile local exec -T backend python -m pip install -e ".[seed]"
docker compose --env-file .env.local --profile local exec -T backend python -m app.seeding plan --dataset local-review-v3 --profile manual --seed 20261105 --output-dir /app/.artifacts/seeding
```

`plan` tidak memerlukan akses database atau password demo. Bind mount lokal mempertahankan artefak di `backend/.artifacts/seeding/local-review-v3/manifest.json` pada host. Ikuti [seeding](seeding.md) untuk memilih environment database dan memasok password saat `apply`. Gunakan nama dataset baru ketika generator/konfigurasi berubah; data existing tetap dipertahankan.

## Menghentikan stack dan deployment

Dari **root repository**:

```powershell
docker compose --env-file .env.local --profile local down
```

Named volume database tetap tersedia. Untuk staging/production, ikuti [deployment](deployment.md): template/project name terpisah, migration sebelum startup API/worker, frontend statis, base URL bundle `/api`, dan TLS eksternal.
