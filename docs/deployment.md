# Deployment Staging dan Production

Panduan ini memakai profile deployment pada [`docker-compose.yml`](../docker-compose.yml). Semua perintah host dijalankan dari **root repository menggunakan PowerShell**. Perintah `sh -c` dijalankan oleh shell di dalam container.

## Menyiapkan environment

Salin template untuk environment yang akan dijalankan:

```powershell
Copy-Item .env.staging.example .env.staging
Copy-Item .env.prod.example .env.prod
```

Isi file yang akan digunakan sebelum menjalankan Compose:

| Variabel | Pengaturan |
| --- | --- |
| `APP_ENV_FILE` | `.env.staging` atau `.env.prod`; memilih file environment layanan |
| `DEPLOYMENT_ENV` | `staging` atau `prod`, sesuai profile; database deployment menolak nilai lain |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Credential database; samakan dengan `DATABASE_URL` |
| `DATABASE_URL` | Koneksi `postgresql+asyncpg` dengan hostname `db-deploy` |
| `REDIS_URL` | `redis://redis:6379/0` dalam network Compose |
| `JWT_SECRET` | Secret unik per environment |
| `SUPERADMIN_EMAIL`, `SUPERADMIN_PASSWORD`, `SUPERADMIN_NAME` | Akun bootstrap awal; tidak mengganti akun yang sudah ada |
| `CORS_ORIGINS` | JSON array origin frontend, termasuk scheme dan port jika ada |
| `SMTP_*` | Server, credential, alamat pengirim, security, dan timeout untuk email nyata |
| `INSTITUTION_NAME` | Nama institusi pada laporan |
| `DB_HOST_PORT`, `REDIS_HOST_PORT`, `HTTP_PORT` | Port host yang berbeda antar-environment |
| `UVICORN_WORKERS` | Jumlah proses API; default template 2 |

Gunakan password URL-safe atau percent-encoding pada password dalam `DATABASE_URL`. Nilai credential sebenarnya tetap disimpan di file environment yang diabaikan Git.

`--env-file` memasok substitusi Compose, sedangkan `APP_ENV_FILE` dipakai oleh `env_file` layanan. Variabel environment shell dapat menimpa substitusi file; periksa nilainya jika Compose memakai konfigurasi yang tidak diharapkan.

## Menjalankan stack

Validasi dan jalankan **staging**:

```powershell
docker compose -p nilai-staging --env-file .env.staging --profile staging config --quiet
docker compose -p nilai-staging --env-file .env.staging --profile staging up -d --build --wait
```

Validasi dan jalankan **production**:

```powershell
docker compose -p nilai-prod --env-file .env.prod --profile prod config --quiet
docker compose -p nilai-prod --env-file .env.prod --profile prod up -d --build --wait
```

Gunakan project name yang sama pada seluruh perintah untuk environment tersebut. Project name berbeda memisahkan network dan named volume. Template staging memakai port host database/Redis/HTTP `25432`/`26379`/`28080`; production memakai `35432`/`36379`/`38080`. Port internal container tetap 5432/6379/80 sehingga URL antar-layanan tidak mengikuti port host.

Compose menunggu database sehat, menjalankan layanan `migrate` sampai sukses, lalu memulai API dan worker. Frontend dibangun menjadi aset statis dan dilayani Nginx. Build arg `VITE_API_URL` pada Compose bernilai `/api`; environment runtime Nginx tidak mengubah URL dalam bundle.

## Reverse proxy dan TLS

Port edge hanya dipublikasikan pada loopback host. Arahkan reverse proxy HTTPS eksternal ke `127.0.0.1:HTTP_PORT` dan teruskan header `Host`, `X-Forwarded-For`, serta `X-Forwarded-Proto` yang sesuai request HTTPS.

Proxy dalam repository meneruskan `/api/` ke FastAPI dengan menghapus prefix tersebut; path lain diteruskan ke frontend. Health dan schema OpenAPI tersedia di `/api/health` serta `/api/openapi.json` pada origin frontend.

Swagger pada `/api/docs` saat ini meminta schema dari `/openapi.json` karena aplikasi belum mengatur `root_path` untuk prefix proxy. Path tersebut diteruskan ke frontend, sehingga Swagger di deployment belum dapat memuat schema. Gunakan `/api/openapi.json` untuk memeriksa kontrak API; penyesuaian prefix Swagger memerlukan perubahan konfigurasi aplikasi/proxy.

## Memeriksa deployment

Contoh berikut untuk **production**, dengan `HTTP_PORT=38080`. Sesuaikan project, file environment, profile, dan port bila memeriksa staging.

```powershell
docker compose -p nilai-prod --env-file .env.prod --profile prod ps -a
Invoke-RestMethod http://localhost:38080/api/health
Invoke-RestMethod http://localhost:38080/api/openapi.json
docker compose -p nilai-prod --env-file .env.prod --profile prod exec nginx nginx -t
docker compose -p nilai-prod --env-file .env.prod --profile prod exec backend-deploy alembic current
docker compose -p nilai-prod --env-file .env.prod --profile prod exec backend-deploy python scripts/verify_comments.py
docker compose -p nilai-prod --env-file .env.prod --profile prod exec worker-deploy celery -A app.celery_app:celery_app inspect --timeout=5 ping
```

Pastikan flag `db` dan `redis` pada health bernilai `true`, worker membalas ping, frontend dapat dibuka, serta schema OpenAPI dapat dimuat melalui origin HTTPS publik. Status `ok` pada health tanpa memeriksa kedua flag tidak cukup untuk readiness.

Untuk menelusuri kegagalan migration, API, atau worker:

```powershell
docker compose -p nilai-prod --env-file .env.prod --profile prod logs --tail=100 migrate backend-deploy worker-deploy
docker compose -p nilai-prod --env-file .env.prod --profile prod logs -f worker-deploy
```

Jika `migrate` gagal, periksa log dan perbaiki penyebabnya sebelum mencoba startup kembali. Jangan menjalankan pytest pada database deployment; gunakan [lingkungan disposable](../backend/README.md#menjalankan-tests-pada-database-disposable).

## Memperbarui deployment

Sebelum menerapkan revision yang membawa migration, buat backup database. Contoh **production**, dari root repository:

```powershell
docker compose -p nilai-prod --env-file .env.prod --profile prod exec db-deploy sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/nilai-before-update.dump'
docker compose -p nilai-prod --env-file .env.prod --profile prod cp db-deploy:/tmp/nilai-before-update.dump ../nilai-before-update.dump
```

Simpan backup di luar repository dan pastikan tersedia sebelum update. Setelah checkout revision yang akan dijalankan, rebuild dan ulangi pemeriksaan deployment:

```powershell
docker compose -p nilai-prod --env-file .env.prod --profile prod up -d --build --wait
```

Perubahan environment backend/worker memerlukan recreate layanan; perubahan konfigurasi frontend memerlukan build baru. Jangan menganggap menjalankan image lama otomatis membalik migration yang sudah diterapkan.

Untuk menghentikan stack **production** sambil mempertahankan named volume database:

```powershell
docker compose -p nilai-prod --env-file .env.prod --profile prod down
```

## Troubleshooting

| Gejala | Pemeriksaan |
| --- | --- |
| Database deployment langsung berhenti | Periksa `DEPLOYMENT_ENV` serta file yang dipilih `APP_ENV_FILE`. |
| Login awal tidak tersedia | Pastikan migration selesai dan konfigurasi seed terisi; seed tidak mereset password akun yang sudah ada. |
| API tidak siap | Periksa flag health, log API, serta kecocokan credential dan hostname `db-deploy`/`redis`. |
| Akses HTTPS gagal tetapi localhost berhasil | Periksa tujuan reverse proxy, sertifikat, DNS, dan penerusan `X-Forwarded-Proto`. |
| Notifikasi tetap menunggu/gagal | Periksa worker ping/log, broker, alamat penerima, konfigurasi SMTP, dan retry admin. |
| Export PDF mengembalikan 503 | Periksa log renderer dan pastikan image backend dibangun menggunakan Dockerfile repository. |
