# Panduan Repository

## Struktur project

Backend memakai FastAPI dan frontend memakai React/TypeScript. Pertahankan pembagian lapisan berikut:

- `backend/app/`: HTTP routers, Pydantic schemas, business services, database repositories, dan SQLAlchemy models.
- `backend/alembic/versions/`: database migrations; `backend/tests/`: tests API dan model.
- `frontend/src/`: komponen, utilitas API bersama, dan Zustand stores. Primitive UI berada di `components/ui/`; aset berada di `src/assets/` dan `public/`.
- `docs/superpowers/`: arsip spesifikasi dan rencana implementasi. Cocokkan fitur yang direncanakan dengan implementasi aktual.
- `docker-compose.yml`: layanan PostgreSQL, Redis, API, worker, frontend, dan proxy.

Gunakan [README utama](README.md), [panduan backend](backend/README.md), [panduan frontend](frontend/README.md), dan [panduan deployment](docs/deployment.md) untuk langkah operasional.

## Perintah development dan pemeriksaan

Dari **root repository**, siapkan `.env.local` dengan hostname `db` dan `redis` untuk koneksi antar-container. Profile `local` diperlukan untuk layanan development:

Port host Docker lokal adalah frontend 15173, API 18000, PostgreSQL 15432, dan Redis 16379. Gunakan variabel `*_HOST_PORT` untuk override. Port internal container tetap digunakan pada URL antar-layanan; browser memakai port host. Staging/production memakai kelompok port 2xxxx/3xxxx sesuai template environment.

```sh
docker compose --env-file .env.local --profile local up -d --wait db redis
docker compose --env-file .env.local --profile local run --build --rm backend alembic upgrade head
docker compose --env-file .env.local --profile local up -d --build --wait
```

Untuk backend di host, gunakan Python 3.11+ dan virtual environment. Jalankan dari **`backend/`** setelah memilih database yang sesuai:

```sh
python -m pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

Jalankan dari **`frontend/`**:

```sh
npm ci
npm run dev
npm test
npm run build
npm run lint
```

`npm run build` melakukan TypeScript check dan menghasilkan aset production; `npm run lint` menjalankan Oxlint.

## Konvensi kode dan dokumentasi

- Python: indentasi empat spasi, nama function/module `snake_case`, class `PascalCase`, dan type annotations.
- TypeScript: indentasi dua spasi, komponen React `PascalCase`, dan function `camelCase`.
- Ikuti konvensi quotation dan semicolon di sekitar kode yang diubah; belum ada formatter yang dikonfigurasi. Utamakan import `@/` untuk modul sumber frontend.
- Tambahkan Alembic migration untuk perubahan schema dan pertahankan komentar tabel/kolom berbahasa Indonesia.
- Gunakan docstring Google-style untuk dokumentasi Python dan JSDoc/TSDoc untuk kontrak TypeScript. Komentar internal menjelaskan alasan logic yang tidak langsung jelas.

## Testing

Backend memakai pytest, pytest-asyncio, dan HTTPX. Gunakan nama file `test_*.py` dan function `test_*`. Jalankan `python -m pytest` dari **`backend/`** hanya pada PostgreSQL disposable yang sudah dimigrasi dan di-seed sesuai [panduan tests backend](backend/README.md#menjalankan-tests-pada-database-disposable).

Beberapa tests memerlukan `admin@example.com` dengan password `admin123`; gunakan credential tersebut hanya pada lingkungan test disposable. Cakup otorisasi, validasi, konflik, dan operasi sukses.

Frontend memakai Vitest dan React Testing Library (`npm test`). Untuk perubahan UI, jalankan juga `npm run build` dan `npm run lint`.

## Commit dan pull request

Ikuti Conventional Commits yang sudah digunakan, misalnya `feat(backend): courses CRUD` atau `fix(backend): handle conflicts`. Pisahkan commit berdasarkan concern.

PR menjelaskan perubahan perilaku, menautkan issue terkait, melaporkan hasil verifikasi, dan menyertakan screenshot untuk perubahan UI. Jelaskan kebutuhan migration dan konfigurasi.

## Konfigurasi dan secrets

Mulai dari `.env.example`. Profile Compose lokal membaca `.env.local`; proses backend langsung membaca `.env` relatif working directory atau environment proses. Untuk frontend host, gunakan `frontend/.env.local`. Template staging/production memilih file layanan melalui `APP_ENV_FILE`.

Jangan commit credential atau file environment aktual. Ganti default JWT secret dan gunakan konfigurasi terpisah untuk development, test, staging, dan production.
