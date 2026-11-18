# Pengembangan Backend

Backend memakai FastAPI, Pydantic, SQLAlchemy async, PostgreSQL, Celery, dan Redis. Untuk stack Docker lengkap, mulai dari [README utama](../README.md).

## Dokumentasi

| Panduan | Isi |
| --- | --- |
| [Arsitektur](../docs/architecture.md) | Lapisan aplikasi, relasi data, dan alur finalisasi |
| [Struktur repository](../docs/structure.md) | File, direktori, dan tanggung jawab modul |
| [Instalasi](../docs/installation.md) | Runtime, environment, dan pilihan Docker/host |
| [API](../docs/api.md) | Endpoint, payload, response, error, dan CLI seeder |
| [Testing](../docs/testing.md) | Database disposable dan cakupan tests |
| [Seeder persisten](../docs/seeding.md) | Dataset manual, pemetaan kasus, dan perintah Docker |
| [Deployment](../docs/deployment.md) | Profile staging/production dan pemeriksaan layanan |

## Arsitektur dan struktur modul

Router mengikat request/response Pydantic dan meneruskan aturan bisnis ke services. Repositories menjalankan query SQLAlchemy, sedangkan models dan Alembic menjaga schema PostgreSQL. Finalisasi menyimpan grades, rankings, dan notification audit sebelum mengantrekan task Celery melalui Redis; kegagalan antrean tidak membatalkan nilai yang sudah final.

| Lokasi | Tanggung jawab |
| --- | --- |
| `app/main.py`, `config.py`, `database.py` | Komposisi API, konfigurasi, dan session async |
| `app/routers/`, `schemas/` | Kontrak HTTP dan validasi field |
| `app/services/`, `repositories/`, `models/` | Aturan akses/penilaian, persistence, dan tabel |
| `app/tasks/`, `celery_app.py` | Pengiriman notifikasi di worker |
| `app/templates/` | Template laporan PDF; XLSX dirakit oleh service reports |
| `app/seeding/` | CLI, generator graph, manifest, dan persistence dataset manual |
| `alembic/versions/` | Migration database |
| `tests/`, `tests/support/` | Tests API/persistence serta guard target disposable |

Python minimal 3.11 ditentukan oleh `pyproject.toml`. Extra `dev` memasang pytest dan tooling laporan untuk tests; extra `seed` memasang Polyfactory dan Faker. Image runtime memasang package dasar serta dependency native PDF, sehingga extra tersebut perlu dipasang terpisah bila menjalankan tests atau seeder di container.

## API di host

Gunakan Python 3.11+. Siapkan `.env.local` dan hostname container sesuai README utama. API native memakai port 8000, sedangkan API Docker dipublikasikan pada 18000. Dari **root repository menggunakan PowerShell**, jalankan dependensi:

```powershell
docker compose --env-file .env.local --profile local up -d --wait db redis
python -m venv backend/.venv
Copy-Item .env.example backend/.env
```

Edit `backend/.env`: template memakai PostgreSQL `localhost:15432` dan Redis `localhost:16379` untuk mengakses Docker dari host. Sesuaikan port jika `DB_HOST_PORT` atau `REDIS_HOST_PORT` diubah, lalu ganti `JWT_SECRET` dan `SUPERADMIN_PASSWORD`. Jangan menyalin hostname `db` dari konfigurasi container untuk proses host. Untuk memakai database/Redis native, ubah URL ke port layanan native tersebut.

Kemudian, dari **root repository menggunakan PowerShell**:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,seed]"
alembic upgrade head
uvicorn app.main:app --reload
```

Pada shell POSIX, gunakan `source .venv/bin/activate` sebagai pengganti perintah aktivasi PowerShell setelah masuk ke `backend/`.

Buka <http://localhost:8000/docs> untuk mencoba API. Konfigurasi dibaca dari `backend/.env` ketika working directory adalah `backend/`; environment proses memiliki prioritas lebih tinggi. Restart proses setelah mengubah konfigurasi.

Export PDF membutuhkan library native dan font. Image backend sudah memasang `libpango-1.0-0`, `libpangoft2-1.0-0`, `libharfbuzz-subset0`, dan `fonts-dejavu-core`. Gunakan Docker untuk menjalankan renderer dengan dependency tersebut, terutama bila development dilakukan di Windows.

## Email dan worker

API mengantrekan task rilis melalui Redis; Celery worker memproses pengirimannya. Untuk menjalankan worker Docker bersama API di host, gunakan koneksi database/Redis yang sama: `localhost` pada API host dan hostname layanan pada `.env.local` milik worker.

Dari **root repository menggunakan PowerShell**:

```powershell
docker compose --env-file .env.local --profile local up -d --build worker
docker compose --env-file .env.local --profile local logs -f worker
```

Untuk worker langsung di host Linux/WSL yang sudah memiliki seluruh dependency, gunakan **shell POSIX** lain dengan virtual environment aktif, dari **`backend/`**. Pada Windows, gunakan worker Docker di atas.

```sh
celery -A app.celery_app:celery_app worker --loglevel=info
```

| Variabel | Pengaturan |
| --- | --- |
| `SMTP_HOST` | Kosong untuk mode mock; isi hostname untuk pengiriman nyata |
| `SMTP_PORT`, `SMTP_SECURITY` | Sesuaikan server: `starttls`, `ssl`, atau `none` |
| `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | Credential dan alamat pengirim |
| `SMTP_TIMEOUT` | Timeout koneksi, default 10 detik |

Pada mode mock, worker mencatat pengiriman di log tanpa menghubungi SMTP. Status `sent` pada mode ini bukan bukti email nyata diterima. `notified` pada respons finalisasi menghitung task yang diterima antrean. Superadmin dapat memantau dan mengulang pengiriman melalui halaman Notifikasi.

Halaman Notifikasi dibuka dari ikon bell di header. UI menyediakan retry untuk record `failed`; endpoint retry juga menerima status unsent lain sesuai aturan service. Record `sent` menolak retry.

## Migration dan pemeriksaan schema

Dengan virtual environment aktif, jalankan dari **`backend/` menggunakan PowerShell** pada database tujuan yang sudah dipilih:

```powershell
alembic current
alembic upgrade head
python scripts/verify_comments.py
```

Untuk perubahan schema baru, dari **`backend/` menggunakan PowerShell**:

```powershell
alembic revision --autogenerate -m "describe schema change"
```

Tinjau revision sebelum menjalankan `upgrade`. Pertahankan komentar tabel/kolom berbahasa Indonesia dan jangan mengubah migration yang sudah diterapkan. `verify_comments.py` memeriksa metadata tabel/kolom pada schema PostgreSQL `public`, bukan komentar source code.

## Seeder untuk pengujian manual

Bootstrap `app.services.seed.seed_superadmin` hanya menyiapkan akun awal. CLI `python -m app.seeding` menyiapkan dataset akademik tambahan untuk pengujian manual dan sample positif/negatif. Dari **`backend/`** dengan extra `seed` terpasang, buat rencana tanpa koneksi database:

```powershell
python -m app.seeding plan --dataset backend-review-v3 --profile manual --seed 20261105
```

Manifest berada di `.artifacts/seeding/<dataset>/manifest.json` relatif working directory; perintah di atas menulis ke `backend/.artifacts/seeding/` pada host. Generator versi 3 membatasi graph pada 5–15 mata kuliah, 2–5 kelas per mata kuliah, dan 5–15 mahasiswa terdaftar per kelas. Profile `manual` membuat 5–15 sample per kasus dengan batas 25.000 row; `light-load` membuat 10–30 sample dengan batas 100.000 row.

`apply` menambahkan dataset pada database development yang dipilih eksplisit melalui `DATABASE_URL`, memerlukan `APP_ENV=development` atau `local`, `SEED_PASSWORD`, dan SMTP nonaktif. Rerun mempertahankan dataset dan edit manual; pakai nama dataset baru untuk initial state baru. `inspect` memeriksa keberadaan ID tanpa memperbaiki data, lalu memperbarui observasi dalam manifest. Ikuti [panduan seeder](../docs/seeding.md) untuk perintah apply/inspect di host dan Docker, penyimpanan artefak, serta pemetaan aktor/kasus.

## Menjalankan tests pada database disposable

Untuk alur seed data manual yang tetap tersimpan, lihat [docs/seeding.md](../docs/seeding.md). Seeder hanya menambahkan dataset baru dan mempertahankan perubahan human pada dataset yang sudah ada.

Tests backend dapat melakukan commit dan menghapus data fixture. Gunakan container test tersendiri; jangan arahkan pytest ke database development, staging, atau production. Contoh berikut memakai credential khusus test yang diharapkan beberapa tests: `admin@example.com` / `admin123`.

Dari **root repository menggunakan PowerShell**, siapkan network dan database/Redis tanpa mount data aplikasi:

```powershell
docker network create nilai-test
docker run -d --rm --name nilai-test-db --network nilai-test -e POSTGRES_PASSWORD=test-only -e POSTGRES_DB=grades_test postgres:18
docker run -d --rm --name nilai-test-redis --network nilai-test redis:7-alpine
docker exec nilai-test-db pg_isready -U postgres -d grades_test
docker exec nilai-test-redis redis-cli ping
docker build -t nilai-backend-test ./backend
```

Ulangi `pg_isready` sampai berhasil dan pastikan Redis membalas `PONG` sebelum melanjutkan. Buka shell container test dari **root repository menggunakan PowerShell**:

```powershell
docker run --rm -it --network nilai-test `
  -e DATABASE_URL=postgresql+asyncpg://postgres:test-only@nilai-test-db:5432/grades_test `
  -e TEST_DATABASE_URL=postgresql+asyncpg://postgres:test-only@nilai-test-db:5432/grades_test `
  -e TEST_REDIS_URL=redis://nilai-test-redis:6379/0 `
  -e TEST_DATABASE_DISPOSABLE=1 `
  -e REDIS_URL=redis://nilai-test-redis:6379/0 `
  -e JWT_SECRET=local-test-only-secret-not-for-deployment `
  -e SMTP_HOST= `
  -e SUPERADMIN_EMAIL=admin@example.com `
  -e SUPERADMIN_PASSWORD=admin123 `
  nilai-backend-test sh
```

Di dalam **shell container**, working directory adalah **`/app`**. Instal extra test, terapkan migration, dan seed akun secara eksplisit karena HTTPX ASGI tests tidak menjalankan startup aplikasi:

```sh
python -m pip install -e ".[dev,seed]"
alembic upgrade head
python -c "import asyncio; from app.services.seed import seed_superadmin; asyncio.run(seed_superadmin())"
python scripts/verify_comments.py
python -m pytest
```

Guard `tests/conftest.py` mewajibkan tiga variabel `TEST_*` di atas dan mengalihkan koneksi aplikasi sebelum memuat runtime modules. Untuk menjalankan tests di host, gunakan variabel yang sama dengan alamat PostgreSQL disposable yang nama databasenya berakhiran `_test`; jangan arahkan ke database development untuk pengujian manual. Guard memvalidasi konfigurasi eksplisit dan urutan import, tetapi operator tetap bertanggung jawab menyediakan resource disposable.

Panduan untuk membuat dan memeriksa dataset manual append-only, termasuk variasi kasus dan pemetaan multi-mata-kuliah, ada di [panduan seeder](../docs/seeding.md). Jangan arahkan pytest ke database yang digunakan human untuk pengujian manual.

Untuk membatasi skenario, jalankan `python -m pytest tests/test_scores.py -q` di shell container yang sama. Keluar dengan `exit`, lalu bersihkan resource test dari **root repository menggunakan PowerShell**:

```powershell
docker stop nilai-test-db nilai-test-redis
docker network rm nilai-test
```

Container dibuat dengan `--rm`; data database test tidak dipertahankan setelah dihentikan.

## Menambah atau mengubah fitur

- Tempatkan kontrak request/response di `app/schemas/` dan adapter HTTP di `app/routers/`.
- Letakkan otorisasi resource dan aturan bisnis di `app/services/`; query SQLAlchemy berada di `app/repositories/`.
- Periksa batas transaksi repository sebelum menambah operasi: beberapa melakukan commit sendiri, sedangkan alur penilaian memakai transaksi milik service.
- Ubah `app/models/` bersama Alembic revision jika schema berubah. Tambahkan tests untuk akses, validasi, konflik, dan hasil sukses di `tests/`.
- Gunakan docstring Google-style untuk kontrak module/class/function. Gunakan `#` untuk alasan logic, transaksi, atau batasan yang tidak langsung jelas. Detail internal endpoint dapat ditempatkan setelah `\f` agar tidak tampil di Swagger.

## Troubleshooting

| Gejala | Pemeriksaan |
| --- | --- |
| Koneksi database/Redis gagal | Cocokkan hostname proses host versus container, port, dan flag `/health`. |
| Tabel belum tersedia | Periksa `alembic current` dan jalankan migration pada database tujuan. |
| Login bootstrap gagal | Pastikan migration selesai dan variabel seed terisi. Seed tidak mengganti password email yang sudah terdaftar. Untuk memunculkan error seed, jalankan perintah seed eksplisit di atas dalam environment aplikasi yang sesuai. |
| PDF mengembalikan 503 | Periksa dependency renderer; gunakan image backend dengan library native terpasang. |
| Notifikasi tertahan | Periksa worker, `REDIS_URL`, alamat email mahasiswa, dan catatan pengiriman admin. |
