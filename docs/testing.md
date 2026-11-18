# Pengujian

## Backend: PostgreSQL disposable

Suite memakai pytest, pytest-asyncio, dan HTTPX ASGI transport. Test dapat melakukan commit dan menghapus fixture. Gunakan instance PostgreSQL disposable terpisah. Beberapa test memerlukan `admin@example.com` / `admin123`; seed credential ini hanya pada environment test tersebut.

Dari **root repository menggunakan PowerShell**, buat resource terisolasi tanpa mount data aplikasi:

```powershell
docker network create nilai-test
docker run -d --rm --name nilai-test-db --network nilai-test -e POSTGRES_PASSWORD=test-only -e POSTGRES_DB=grades_test postgres:18
docker run -d --rm --name nilai-test-redis --network nilai-test redis:7-alpine
docker exec nilai-test-db pg_isready -U postgres -d grades_test
docker exec nilai-test-redis redis-cli ping
docker build -t nilai-backend-test ./backend
```

Ulangi `pg_isready` sampai berhasil; pastikan Redis membalas `PONG`. Buka container test:

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

Di dalam **shell POSIX container pada `/app`**:

```sh
python -m pip install -e ".[dev,seed]"
alembic upgrade head
python -c "import asyncio; from app.services.seed import seed_superadmin; asyncio.run(seed_superadmin())"
python scripts/verify_comments.py
python -m pytest
```

HTTPX ASGI transport tidak menjalankan startup lifespan sehingga bootstrap seed harus eksplisit. Sebelum mengimpor module runtime, `tests/conftest.py` mewajibkan `TEST_DATABASE_URL` (URL PostgreSQL async dengan nama database berakhiran `_test`), `TEST_REDIS_URL`, dan `TEST_DATABASE_DISPOSABLE=1`. Guard mengalihkan `DATABASE_URL`/`REDIS_URL` dan mengosongkan SMTP agar test tidak memakai environment manual sebagai fallback. File tersebut juga mengadaptasi pemanggilan lama `AsyncClient(app=...)` ke ASGI transport. Pytest memakai async mode dan default test loop scope `session`.

Untuk membatasi test pada container disposable yang sama:

```sh
python -m pytest tests/test_scores.py tests/test_score_clearing.py -q
python -m pytest tests/test_finalization.py tests/test_finalization_concurrency.py -q
python -m pytest tests/test_reports.py -q
python -m pytest tests/test_seed_cli.py tests/test_seed_generation.py tests/test_seed_persistence.py tests/test_seed_scenarios.py tests/test_test_database_guard.py -q
```

Keluar dengan `exit`, lalu bersihkan resource dari **root repository menggunakan PowerShell**:

```powershell
docker stop nilai-test-db nilai-test-redis
docker network rm nilai-test
```

Container memakai `--rm` sehingga penghentian menghapus data disposable tersebut.

## Cakupan test backend

| Area | File pada `backend/tests/` |
| --- | --- |
| Identitas/akun | `test_auth.py`, `test_users.py`, `test_user_model.py` |
| Akses/data akademik | `test_courses.py`, `test_classes.py`, `test_students.py`, serta test model course/class |
| Validasi penilaian | `test_components.py` |
| Skor/pengosongan/perhitungan | `test_scores.py`, `test_score_clearing.py` |
| Rilis/ranking/concurrency | `test_finalization.py`, `test_finalization_concurrency.py` |
| Read model | `test_history.py`, `test_dashboard.py` |
| Laporan/pengiriman | `test_reports.py`, `test_notifications.py`, `test_mailer.py` |
| Infrastruktur/kontrak | `test_health.py`, `test_verify_comments.py`, `test_academic_ui.py` |
| Graph seed/CLI/persistence | `test_seed_generation.py`, `test_seed_cli.py`, `test_seed_persistence.py` |
| Kasus API hasil generator dan isolasi target | `test_seed_scenarios.py`, `test_test_database_guard.py` |

Cakupan tersebut meliputi otorisasi, validasi, konflik, dan operasi sukses. Test laporan membutuhkan tooling PDF/workbook; image menyediakan dependensi native PDF. `verify_comments.py` memeriksa metadata tabel/kolom PostgreSQL pada schema `public`, bukan komentar source.

Test seed mencakup reproduksibilitas, cardinality, pemetaan foreign key, batas row, manifest, preservasi anchor existing, rollback saat konflik, dan apply bersamaan. Sample API memeriksa respons positif/negatif dan state yang tetap sama saat mutasi ditolak. Fixture menambah graph sendiri ke database disposable yang dipilih; dataset manual persisten tidak boleh menjadi target. [Seeding manual](seeding.md) merupakan alur terpisah tanpa command cleanup/reset.

## Pemeriksaan frontend

Dari **`frontend/` menggunakan PowerShell**:

```powershell
npm ci
npm test
npm run build
npm run lint
```

Vitest berjalan sekali dengan jsdom, React Testing Library, setup/cleanup bersama, serta alias `@/` yang sesuai Vite. API dimock sehingga tidak membutuhkan database. Build menjalankan TypeScript check kemudian bundling Vite; lint memakai Oxlint.

Perintah untuk test tertentu:

```powershell
npm test -- src/features/grades/draft.test.ts
npm test -- src/features/grades/GradeEntryGrid.test.tsx
npm test -- src/features/analytics/AnalyticsPages.test.tsx
npm test -- src/features/users/UsersPage.test.tsx
npm test -- src/components/data-table/DataTable.test.tsx
```

Test yang tersedia mencakup koordinasi draft save, pengosongan skor, grid nilai, data/halaman analisis, dialog/filter akun, UI notifikasi, tabel course/class, roster, direktori mahasiswa, widget dashboard, layout/navigasi, tabel bersama, dan download. Manifest package tidak mengatur coverage threshold atau coverage script. Jalankan perintah dari `frontend/`; package root tidak menyediakan application test runner.

## Pemeriksaan runtime

Dari **root repository**:

```powershell
Invoke-RestMethod http://localhost:18000/health
docker compose --env-file .env.local --profile local ps
```

Pastikan `db` dan `redis` bernilai `true`. Uji login, persiapan kelas, draft save, rilis, dan laporan memakai dataset akademik khusus uji. HTTP 200 saja belum membuktikan kesiapan dependensi. Lihat [pemeriksaan deployment](deployment.md#memeriksa-deployment) untuk probe migration/worker pada deployment.

Untuk pytest di host, isi tiga variabel `TEST_*` yang sama dengan alamat host resource yang disiapkan sebagai disposable. Guard menegakkan konfigurasi target eksplisit; guard tidak menyediakan server test maupun membuktikan bahwa server existing aman untuk dihapus.
