# Sistem Input & Rekap Nilai

Panduan menjalankan dan mengembangkan aplikasi pengelolaan nilai berbasis FastAPI dan React.

## Prasyarat

- Git dan Docker dengan Linux containers serta Docker Compose v2.
- Untuk development di host: Python 3.11+ dan Node.js sesuai [manifest frontend](frontend/package.json).

Semua perintah di halaman ini dijalankan dari **root repository menggunakan PowerShell**.

## Menjalankan stack lokal

1. Siapkan file environment:

   ```powershell
   Copy-Item .env.example .env.local
   ```

2. Edit `.env.local`. Ganti `JWT_SECRET` dan `SUPERADMIN_PASSWORD`, lalu gunakan hostname layanan untuk koneksi antar-container:

   ```dotenv
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/grades
   REDIS_URL=redis://redis:6379/0
   ```

   Contoh ini memakai kredensial database bawaan untuk lokal. Jika menggantinya, samakan `POSTGRES_USER`, `POSTGRES_PASSWORD`, dan `POSTGRES_DB` dengan `DATABASE_URL`.

3. Validasi konfigurasi, jalankan database/Redis, lalu terapkan migration sebelum API mulai:

   ```powershell
   docker compose --env-file .env.local --profile local config --quiet
   docker compose --env-file .env.local --profile local up -d --wait db redis
   docker compose --env-file .env.local --profile local run --build --rm backend alembic upgrade head
   docker compose --env-file .env.local --profile local up -d --build --wait
   ```

4. Periksa API setelah startup:

   ```powershell
   Invoke-RestMethod http://localhost:18000/health
   ```

   Pastikan `db` dan `redis` bernilai `true`. Field `status: ok` saja tidak membuktikan koneksi dependensi siap.

| Layanan | Alamat lokal |
| --- | --- |
| Frontend | <http://localhost:15173> |
| API | <http://localhost:18000> |
| Swagger UI | <http://localhost:18000/docs> |

Login menggunakan `SUPERADMIN_EMAIL` dan `SUPERADMIN_PASSWORD` dari `.env.local`. Startup membuat akun jika email belum terdaftar. Mengubah environment tidak mengganti password akun yang sudah ada.

## Port Docker pada host

| Layanan | Port internal container | Lokal | Staging | Production |
| --- | --- | --- | --- | --- |
| PostgreSQL | 5432 | 15432 | 25432 | 35432 |
| Redis | 6379 | 16379 | 26379 | 36379 |
| API lokal | 8000 | 18000 | — | — |
| Vite lokal | 5173 | 15173 | — | — |
| Nginx deployment | 80 | — | 28080 | 38080 |

Ubah `DB_HOST_PORT`, `REDIS_HOST_PORT`, `BACKEND_HOST_PORT`, `FRONTEND_HOST_PORT`, atau `HTTP_PORT` pada file environment untuk memilih port host lain. Template lokal menurunkan `VITE_API_URL` dan `CORS_ORIGINS` dari port tersebut; bila mengisi URL/origin secara eksplisit, sesuaikan juga nilainya.

Koneksi antar-container tetap memakai port internal, misalnya `db:5432` dan `redis:6379`. Worker dan migration tidak memublikasikan port; API/frontend deployment diakses melalui Nginx. Mapping host ini memungkinkan Docker berjalan bersama layanan native pada port defaultnya.

## Memilih file environment

| Cara menjalankan | File | Host koneksi |
| --- | --- | --- |
| API/worker dalam Compose lokal | `.env.local` di root | PostgreSQL `db`, Redis `redis` |
| API langsung di host, working directory `backend/` | `backend/.env` atau environment proses | `localhost` dan port yang dipublikasikan Docker |
| Vite langsung di host | `frontend/.env.local` | API Docker: `http://localhost:18000`; API native: `http://localhost:8000` |
| Staging/production | `.env.staging` / `.env.prod` melalui `APP_ENV_FILE` | PostgreSQL `db-deploy`, Redis `redis` |

`--env-file` memasok substitusi Compose; file pada `env_file` memasok environment container. Pada profile `local`, `env_file` tetap menunjuk `.env.local`. Proses backend di host membaca `.env` relatif terhadap working directory dan mengutamakan environment proses.

Jangan commit file environment aktual atau secret. Untuk memakai nama institusi pada laporan, isi `INSTITUTION_NAME`. `SMTP_HOST` kosong mengaktifkan mode mock; lihat [panduan backend](backend/README.md#email-dan-worker).

## Perintah harian

```powershell
docker compose --env-file .env.local --profile local ps
docker compose --env-file .env.local --profile local logs -f backend worker
docker compose --env-file .env.local --profile local exec backend alembic current
docker compose --env-file .env.local --profile local exec backend python scripts/verify_comments.py
docker compose --env-file .env.local --profile local down
```

`down` menghentikan stack dan mempertahankan named volume database. Jalankan kembali perintah `up` setelah layanan dihentikan.

## Struktur dan panduan lanjutan

| Lokasi | Panduan |
| --- | --- |
| [`backend/`](backend/README.md) | API, worker, migration, development di host, dan tests dengan database disposable |
| [`frontend/`](frontend/README.md) | Vite, konfigurasi API, struktur fitur, tests, build, dan lint |
| [`docs/deployment.md`](docs/deployment.md) | Staging/production, reverse proxy, pemeriksaan layanan, dan update |
| [`AGENTS.md`](AGENTS.md) | Konvensi perubahan kode, dokumentasi, commit, dan PR |

`docs/superpowers/` menyimpan arsip spesifikasi dan progres implementasi. Gunakan konfigurasi dan panduan aktif di atas untuk menjalankan aplikasi saat ini.
