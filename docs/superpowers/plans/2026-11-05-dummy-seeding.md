# Dummy Seeding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Menyediakan dataset persisten untuk pengujian manual human dan data kasus positif/negatif bervariasi untuk pytest, tanpa cleanup otomatis menyentuh dataset manual.

**Architecture:** Polyfactory + Faker membangun graph dan katalog request secara deterministik dari konfigurasi seeded. CLI menyimpan graph dalam satu transaksi serta menghasilkan manifest/checklist, sedangkan pytest memakai generator yang sama di PostgreSQL/Redis disposable dengan guard sebelum koleksi. Profil `light-load` menghasilkan data lebih besar; load runner bukan bagian pekerjaan ini.

**Tech Stack:** Python 3.11+, SQLAlchemy async/asyncpg, PostgreSQL, Polyfactory, Faker `id_ID`, pytest/pytest-asyncio, HTTPX, argparse, dataclasses, dan pathlib.

**Spec:** [2026-11-05-dummy-seeding-design.md](../specs/2026-11-05-dummy-seeding-design.md).

**Status:** Implementasi berlangsung pada branch `feat/dummy-seeding`. User menyetujui eksekusi plan. Progres dan hasil verifikasi dicatat di ledger sesi; checklist task belum ditandai lengkap sebelum semua bukti tersedia.

## Global Constraints

1. Database manual tidak pernah menjadi target pytest. Cleanup tests hanya menyentuh database disposable yang dipilih eksplisit.
2. Seeder persisten tidak menyediakan reset, truncate, drop, atau penghapusan otomatis, termasuk ketika dijalankan ulang atau gagal.
3. Dataset yang sudah ada tidak ditimpa, diperbaiki otomatis, atau diisi ulang; perubahan human tetap dipertahankan. Dataset baru menggunakan nama dataset baru.
4. Setiap kasus yang terdaftar menghasilkan minimal lima contoh; jumlah, atribut, dan target bervariasi dalam batas profil. Kasus tidak dipilih secara acak sehingga ada yang terlewat.
5. Kasus batas wajib tetap hadir di samping variasi acak. Nilai nol, maksimum, 44.99/45.00, skor seri, null, dan field yang dihilangkan tidak bergantung peluang muncul.
6. Hasil generator dapat direproduksi dengan dataset name, random seed, profile, generator version, dependency versions, dan reference time yang sama. Timestamp server serta hash bcrypt bersalt tidak dijanjikan identik byte demi byte.
7. Data dan payload negatif dipisahkan: permintaan tidak sah dikirim ke API, bukan dipaksakan menjadi record yang melanggar constraint database.
8. Gunakan Polyfactory + Faker dengan locale `id_ID`, Python 3.11+, SQLAlchemy async, dan PostgreSQL. Factory menggunakan build/flush; pemanggil memiliki batas commit.
9. Tidak ada publish Celery atau koneksi SMTP selama konstruksi dataset. Notifikasi contoh diberi label simulasi dalam manifest.
10. Seeder menggunakan satu transaksi untuk penambahan satu dataset; benturan constraint membatalkan penambahan itu tanpa menghapus data yang sudah ada.

Tambahan operasional: pertahankan startup `services/seed.py`; tidak ada endpoint/UI/migration baru, Hypothesis, load runner, atau CI baru. Jangan mengikutsertakan perubahan dokumentasi lain yang sudah ada dalam working tree ke commit implementasi tanpa meninjau scope.

## Review Focus

1. Import engine atau task sebelum guard dapat mengikat koneksi ke database manual: uji subprocess membuktikan pengalihan/penolakan sebelum test collection (Task 1).
2. Rerun setelah human mengedit/menghapus record, atau manifest tertinggal setelah commit: tidak boleh recreate/overwrite; uji snapshot dan rekonsiliasi read-only (Tasks 3 dan 5).
3. Variasi login mencapai limiter 30/minute sebelum tujuan testcase: isolasi fixture fungsional dan uji limiter tersendiri tanpa mengubah limiter aplikasi (Task 4).
4. Banyak case samples menghasilkan graph melebihi batas, atau random menghilangkan kasus batas: uji preflight seluruh tabel dan coverage per case ID (Task 2).
5. Seeder memicu email atau menghasilkan final/ranking/notifikasi yang tidak konsisten: uji publisher/SMTP fail-on-call serta assertions graph release (Task 3).

## Peta file dan tanggung jawab

| File | Perubahan dan tanggung jawab |
| --- | --- |
| `backend/app/seeding/__init__.py` | Package baru, tanpa efek samping/import engine |
| `backend/app/seeding/config.py` | Profil, batas volume, RNG/seed/reference time, fingerprint konfigurasi |
| `backend/app/seeding/factories.py` | Base Polyfactory dan factory sepuluh model, tanpa commit otomatis |
| `backend/app/seeding/scenarios.py` | Case catalog, sample recipes, actor/target states, graph planning |
| `backend/app/seeding/dataset.py` | Persistence graph atomik, anchor lookup, summary dan preservasi rerun |
| `backend/app/seeding/manifest.py` | JSON/checklist, redaction, penulisan atomik, observasi record |
| `backend/app/seeding/__main__.py` | CLI argparse `plan`, `apply`, `inspect`; validasi environment sebelum engine |
| `backend/tests/support/__init__.py` | Namespace helper tests |
| `backend/tests/support/database_guard.py` | Guard murni untuk target disposable sebelum app import |
| `backend/tests/support/seed_data.py` | Fixture/context dan executor request samples yang reusable |
| `backend/tests/conftest.py` | Pasang guard, pertahankan shim HTTPX yang sudah ada |
| `backend/tests/test_test_database_guard.py` | Subprocess dan unit proof target pytest |
| `backend/tests/test_seed_generation.py` | RNG, batas, coverage katalog, boundary dan graph tanpa DB |
| `backend/tests/test_seed_persistence.py` | Apply/rerun/rollback/final graph di PostgreSQL disposable |
| `backend/tests/test_seed_cli.py` | CLI/env/manifest dan pengujian CLI pada `manual_fixture` |
| `backend/tests/test_seed_scenarios.py` | Case samples positif/negatif lewat HTTPX |
| `backend/tests/test_seed_preservation.py` | Proof dua database disposable A/B, human edits tetap ada |
| `backend/pyproject.toml` | Extra `seed` berisi versi tepat Polyfactory/Faker yang kompatibel |
| `.env.test.example`, `.gitignore` | Contoh environment test, abaikan `.env.test` dan artefak seeder |
| `docs/seeding.md` | Panduan manusia, lifecycle, katalog kasus dan light-load dataset |
| `backend/README.md`, `docs/testing.md`, `README.md` | Tautan, extra dependencies, prosedur test dengan guard |

Gunakan folder yang sudah ada untuk fitur lainnya; tidak diperlukan perubahan frontend. Jika pemisahan file berbeda diperlukan, pertahankan interfaces berikut dan jelaskan alasan dalam review.

## Kontrak antartugas

- `SeedConfig` adalah frozen dataclass: `dataset: str`, `profile: Literal["manual", "light-load"]`, `seed: int`, `min_samples: int`, `max_samples: int`, `max_rows: int`, `reference_time: datetime`, `generator_version: str`.
- `resolve_config(*, dataset: str, profile: str = "manual", seed: int | None = None, min_samples: int | None = None, max_samples: int | None = None, max_rows: int | None = None, reference_time: datetime | None = None) -> SeedConfig` ada di `config.py`. Default manual 5–15/25.000 row; light-load 10–30/100.000; minimum lima, hard ceiling 100.000; reference time default UTC 2026-01-01; generator version `"1"`. Dataset name hanya `[a-z0-9][a-z0-9-]{0,39}`.
- `CaseSpec` dan `CaseSample` ada di `scenarios.py`. Spec memiliki `case_id`, `operation: tuple[str, str] | None`, `manual_support: Literal["ui", "api", "automated-only"]`, `mutates: bool`, dan `expected_status: int`. Sample memiliki `sample_id`, `case_id`, `actor_key: str | None`, `method`, `path`, `payload: object`, `expected_status`, serta `assertion_keys: tuple[str, ...]`. Payload token/password menggunakan placeholder runtime.
- `SeedPlan` di `scenarios.py`: `config: SeedConfig`, `anchor_id: UUID`, `objects: tuple[Base, ...]` dalam urutan dependency, `samples: tuple[CaseSample, ...]`, `counts: dict[str, int]`, dan `fingerprint: str`. Factory melengkapi ID/key/reproducible fields secara eksplisit; password hashes merupakan placeholder internal sampai apply.
- `build_plan(config: SeedConfig) -> SeedPlan` tanpa koneksi DB/password; `CASE_CATALOG: tuple[CaseSpec, ...]`; `canonical_plan(plan: SeedPlan) -> dict[str, object]` mengabaikan hash password dan timestamp server untuk assertion reproduksibilitas.
- `ApplyResult` di `dataset.py`: `status: Literal["created", "existing"]`, `anchor_id: UUID`, `counts: dict[str, int]`. `apply_plan(db: AsyncSession, plan: SeedPlan, *, password: str) -> ApplyResult` memiliki transaksi session yang belum aktif; caller test dapat mengikat session ke outer transaction/savepoint. Rerun tidak memutasi object tersimpan.
- `write_manifest(output_dir: Path, plan: SeedPlan, *, state: Literal["planned", "applied"]) -> Path`, `read_manifest(output_dir: Path, dataset: str) -> dict[str, object]`, dan `inspect_dataset(db: AsyncSession, manifest: dict[str, object]) -> dict[str, object]` ada di `manifest.py`. Jangan menambahkan password/token/URL berkredensial ke output.
- `configure_test_environment(env: MutableMapping[str, str]) -> None` ada di test support guard: validasi tiga variabel test, set database/Redis test dan SMTP mock, tanpa koneksi atau import `app.database`.
- `seeded_context` fixture di test support menghasilkan `db`, `client`, `plan`, dan pemetaan actor headers; `execute_sample(context, sample: CaseSample) -> Response` menyelesaikan placeholder runtime dan melakukan assertions berdasarkan case ID. Tidak ada `eval`/eksekusi kode dari manifest.

## Lingkungan verifikasi yang digunakan saat eksekusi

Semua tests DB hanya pada container baru yang dedicated. **Jangan menjalankan perintah ini pada tahap perencanaan.** Nama database A adalah `manual_fixture` dan B adalah `grades_test`; keduanya milik container di bawah, bukan stack `.env.local` pengguna.

Dari root repository dengan PowerShell:

```powershell
docker network create nilai-seeding-tests
docker run -d --rm --name nilai-seeding-pg --network nilai-seeding-tests -e POSTGRES_PASSWORD=test-only -e POSTGRES_DB=grades_test postgres:18
docker run -d --rm --name nilai-seeding-redis --network nilai-seeding-tests redis:7-alpine
docker exec nilai-seeding-pg pg_isready -U postgres -d grades_test
docker exec nilai-seeding-redis redis-cli ping
```

Tunggu readiness berhasil, lalu:

```powershell
docker exec nilai-seeding-pg createdb -U postgres manual_fixture
docker build -t nilai-seeding-backend-test ./backend
docker run --rm -it --network nilai-seeding-tests `
  -e DATABASE_URL=postgresql+asyncpg://postgres:test-only@nilai-seeding-pg:5432/grades_test `
  -e TEST_DATABASE_URL=postgresql+asyncpg://postgres:test-only@nilai-seeding-pg:5432/grades_test `
  -e TEST_REDIS_URL=redis://nilai-seeding-redis:6379/0 `
  -e TEST_DATABASE_DISPOSABLE=1 `
  -e SEED_PRESERVATION_DATABASE_URL=postgresql+asyncpg://postgres:test-only@nilai-seeding-pg:5432/manual_fixture `
  -e SMTP_HOST= `
  -e JWT_SECRET=disposable-seeding-test-only `
  -e SUPERADMIN_EMAIL=admin@example.com `
  -e SUPERADMIN_PASSWORD=admin123 `
  nilai-seeding-backend-test sh
```

Di shell POSIX container `/app`, setelah extra `seed` ditambahkan pada Task 2:

```sh
python -m pip install -e ".[dev,seed]"
alembic upgrade head
DATABASE_URL="$SEED_PRESERVATION_DATABASE_URL" alembic upgrade head
python -c "import asyncio; from app.services.seed import seed_superadmin; asyncio.run(seed_superadmin())"
```

Task 1 belum memerlukan extra `seed`; gunakan `python -m pip install -e ".[dev]"`. Jangan gunakan global `DATABASE_URL` manual untuk pytest. Perintah pytest tiap task berikut dijalankan dari `/app` pada shell test tersebut. Setelah seluruh verifikasi, hanya container khusus ini yang boleh dihentikan/dihapus. Tidak ada cleanup pada stack/database/artefak seeder manual pengguna.

## Task 1: Lindungi seluruh koneksi pytest sebelum test collection

**Files:** Create `backend/tests/support/__init__.py`, `backend/tests/support/database_guard.py`, `backend/tests/test_test_database_guard.py`, `.env.test.example`; modify `backend/tests/conftest.py`, `.gitignore`, dan bagian disposable tests `backend/README.md`.

**Interfaces:** Consumes process environment. Produces `configure_test_environment` sesuai kontrak; guard dijalankan saat conftest dimuat, sebelum test modules mengimpor settings/engine/tasks. Pertahankan shim HTTPX.

- [ ] **Step 1: Tulis tests guard yang gagal.** `test_requires_explicit_disposable_target` memeriksa env kosong, opt-in hilang/bukan `1`, DSN bukan PostgreSQL async, atau database bukan suffix `_test` menghasilkan error sebelum app import. `test_redirects_all_test_connections` memberi env awal manual dan target test lalu memeriksa `DATABASE_URL == TEST_DATABASE_URL`, `REDIS_URL == TEST_REDIS_URL`, `SMTP_HOST == ""`; tidak mencetak secrets. `test_guard_fails_before_collection` menjalankan child pytest yang diberi test module sentinel; env invalid menghasilkan exit nonzero dan sentinel tidak tersentuh. `test_preimported_runtime_is_rejected` memeriksa runtime yang telanjur mengikat settings/engine menyebabkan penolakan. `test_cached_settings_are_cleared_after_configuration` memeriksa get_settings yang sempat dibaca kembali menunjuk target test setelah guard.
- [ ] **Step 2: Jalankan** `python -m pytest tests/test_test_database_guard.py -q`. Harapkan kegagalan karena guard belum tersedia, bukan koneksi ke database pengguna.
- [ ] **Step 3: Implementasikan guard.** Validasi melalui `sqlalchemy.engine.make_url`, semua field wajib dan nama DB; gunakan exception pesan teredaksi. Set environment sebelum import application modules. Jika `app.database`, `app.celery_app`, atau `app.services.auth` sudah diimpor sebelum guard, gagalkan proses alih-alih mencoba mengganti runtime diam-diam. Setelah validasi/konfigurasi berhasil, bersihkan `get_settings` cache sebelum import runtime pertama. Dokumentasikan kontrak opt-in dan extra env test, termasuk pengaruh ke worker/task dalam proses test.
- [ ] **Step 4: Jalankan ulang tests guard**, lalu `python -m pytest tests/test_auth.py tests/test_users.py -q` setelah bootstrap test; harapkan PASS dan DSN test pada assertions. Tests negatif guard memakai subprocess dan tidak menonaktifkan guard parent.
- [ ] **Step 5: Commit hanya file task** dengan pesan `test(backend): isolate pytest from persistent seed data`.

## Task 2: Bangun factory dan katalog variasi dengan jumlah berbatas

**Files:** Create `backend/app/seeding/__init__.py`, `config.py`, `factories.py`, `scenarios.py`, `backend/tests/test_seed_generation.py`; modify `backend/pyproject.toml`.

**Interfaces:** Consumes ORM models dan validation/calculation helpers murni; produces `SeedConfig`, `CaseSpec`, `CaseSample`, `SeedPlan`, `CASE_CATALOG`, `resolve_config`, `build_plan`, `canonical_plan` sesuai kontrak. Tidak mengimpor application engine atau melakukan I/O.

- [ ] **Step 1: Tulis tests generator yang gagal.** `test_replays_same_config` membandingkan canonical plan untuk dataset/seed/reference time sama. `test_each_case_has_distinct_multiple_samples` memeriksa setiap case mendapat 5–15 sample IDs unik pada manual; state/target/payload bervariasi sesuai jenis case. `test_profiles_and_overrides_enforce_limits` memeriksa profil dan input min <5, min>max, max_rows>100.000 ditolak. `test_large_plan_fails_before_database_access` memakai batas terlalu kecil dan memastikan tidak ada engine dibuat. `test_boundaries_and_exact_weights_always_exist` memeriksa semua seed representatif 1, 17, 20261105 memiliki boundary wajib, jumlah bobot Decimal 100.00, kategori UTS/UAS, FK valid, dan zero berbeda dari missing.
- [ ] **Step 2: Jalankan** `python -m pytest tests/test_seed_generation.py -q`; harapkan FAIL karena module/kontrak baru belum ada.
- [ ] **Step 3: Tambahkan extra `seed` dan implementasikan generator.** Verifikasi rilis Polyfactory/Faker yang kompatibel dengan Python 3.11/SQLAlchemy saat eksekusi, pin exact version dalam extra, dan instal `.[dev,seed]`. Gunakan `__faker__` dengan `id_ID`, factory build/flush, RNG lokal dengan child seed SHA-256 atas seed/case/sample (bukan `hash()` Python), UUIDv5, dan key berprefix pendek. Default nilai class/status/role/precision harus valid terhadap model. Generator harus menghitung row setiap tabel sebelum persistence.
- [ ] **Step 4: Definisikan katalog berdasarkan matriks spec.** Setiap operasi GET/POST/PATCH/PUT/DELETE terdaftar dalam OpenAPI memiliki minimal satu case positif atau mapping automated-only yang masuk akal. Beri ID berbeda untuk tiap penyebab negatif di spec: contoh `score.negative`, `score.over_max`, `score.nonfinite`, `component.weight_below`, `component.weight_above`, `finalize.missing_score`, `finalize.empty_roster`, `finalize.repeat`, `authorization.other_lecturer`. Login/token/password placeholders tidak berisi credential asli. Case tanpa input, seperti health, menggunakan variasi kondisi dependency. Resource mutating samples tidak boleh berbagi target yang akan merusak expected state sample lain.
- [ ] **Step 5: Jalankan ulang tests generator.** Tambahkan `test_catalog_maps_all_application_operations` yang membandingkan union operation katalog dengan 43 operasi OpenAPI saat ini, dan `test_catalog_negative_causes_are_not_randomly_omitted` untuk ID wajib dari spec. Harapkan PASS untuk semua seed representatif; jangan mengharuskan setiap pasangan seed menghasilkan jumlah yang berbeda.
- [ ] **Step 6: Commit** `feat(backend): generate varied reproducible seed scenarios`.

## Task 3: Simpan satu dataset atomik dan pertahankan dataset yang sudah ada

**Files:** Create `backend/app/seeding/dataset.py`, `backend/tests/test_seed_persistence.py`; refine graph construction pada `scenarios.py` jika tests menunjukkan dependensi state yang belum lengkap.

**Interfaces:** Consumes `SeedPlan`, current `calculate_final_score`, model constraints, dan ordering ranking existing; produces `ApplyResult` dan `apply_plan`. Tidak membuat engine sendiri dan tidak memanggil finalization service yang melakukan publish/commit sendiri.

- [ ] **Step 1: Tulis tests persistence yang gagal.** `test_apply_commits_one_consistent_graph` memeriksa row/FK/count dan successful login memakai hash dari `SEED_PASSWORD`. `test_released_graph_matches_domain_rules` memeriksa totals, timestamp/by audit, ranking sequential dan tie-break, serta status/timestamp notification simulasi. `test_seed_never_publishes_or_sends_mail` membuat `celery_app.send_task` dan transport SMTP fail-on-call. `test_rerun_preserves_human_changes_and_missing_rows` mengubah nama/skor draft dan menghapus target yang boleh dihapus, lalu mengulang apply; status `existing`, fingerprint data tetap sama seperti setelah edit human. `test_conflict_rolls_back_only_new_dataset` membuat benturan natural key dan memeriksa semua data lama tetap utuh serta tidak ada anchor baru parsial.
- [ ] **Step 2: Jalankan** `python -m pytest tests/test_seed_persistence.py -q` pada `grades_test`; harapkan FAIL untuk fungsi persistence yang belum ada.
- [ ] **Step 3: Implementasikan `apply_plan`.** Dalam satu `db.begin()`, lookup anchor UUIDv5 namespace dataset, return read-only existing jika ada, hash password akun dummy hanya untuk create, insert/flush sesuai dependency, dan commit atomik. Gunakan helper perhitungan/ranking yang tidak memiliki commit/publish, atau query ordering yang sama bila helper memerlukan state yang belum flush. Tangkap benturan sebagai error tanpa DELETE/cleanup. Serialisasi dua apply bersamaan pada dataset sama menggunakan transaksi/advisory lock atau unique anchor; loser tidak boleh menghapus pemenang.
- [ ] **Step 4: Tambahkan `test_simultaneous_apply_preserves_winner`** dengan dua session pada database disposable, lalu jalankan ulang persistence dan generator tests. Harapkan satu dataset konsisten; proses kedua melaporkan existing/conflict terkontrol. Verifikasi field finalized dan snapshot ranking sesuai aturan existing, tanpa perubahan file layanan produksi.
- [ ] **Step 5: Commit** `feat(backend): persist seed datasets without overwriting human edits`.

## Task 4: Jalankan beberapa variasi per kasus melalui pytest/HTTPX

**Files:** Create `backend/tests/support/seed_data.py`, `backend/tests/test_seed_scenarios.py`; modify existing test modules hanya untuk menambahkan regression assertions yang perlu mengakses helper internal existing.

**Interfaces:** Consumes katalog/plan dan `apply_plan`; produces `seeded_context`, `execute_sample`, serta parametrized cases dengan ID `<case_id>:<sample_id>`. Context terikat ke disposable DB dan actor headers hanya hidup di memori.

- [ ] **Step 1: Tulis test runner yang gagal.** `test_generated_case(sample)` menjalankan setiap sample dari katalog manual untuk seed 20261105, memeriksa expected status/detail dan `assertion_keys`; positive writes memeriksa persistence, negative writes memeriksa target tidak berubah. `test_samples_do_not_invalidate_each_other` menjalankan urutan terbalik dan memastikan target mutasi independen. `test_generated_foreign_actor_is_rejected` memeriksa akses lintas dosen/class dengan minimal lima contoh nyata.
- [ ] **Step 2: Jalankan** `python -m pytest tests/test_seed_scenarios.py -q`; harapkan FAIL karena fixtures/executor belum tersedia.
- [ ] **Step 3: Implementasikan fixture dan executor.** Gunakan session savepoint/rollback untuk kasus yang kompatibel; kasus multikoneksi/concurrency tetap memakai resource disposable terpisah dan cleanup ID miliknya. Daftar actor memakai akun dummy atau bootstrap test yang sesuai, bukan akun manusia. Resolve password/token placeholders di memori; panggil service/API nyata untuk aksi yang sedang diuji. Publisher/SMTP difake hanya pada kasus fungsional yang tidak menguji transport; kasus broker/SMTP failure memiliki stub exception eksplisit dan assertions notifikasi/release.
- [ ] **Step 4: Tambahkan isolasi limiter dan assertions domain.** `test_functional_login_samples_do_not_hit_rate_limit` menonaktifkan `limiter.enabled` hanya via fixture monkeypatch scope dan memastikan dipulihkan. `test_login_rate_limit_is_enforced` memakai alamat test khusus, reset storage test, limiter aktif, lalu memeriksa request ke-31 menjadi 429. Tambahkan assertions null/omitted/zero, exact Decimal rounding, audit last writer, repeated release conflict, immutable finalized state, rankings, history visibility, dashboard scope, report attachments, notification filter/retry/sent rejection, dan health/renderer failures terkontrol sesuai katalog.
- [ ] **Step 5: Jalankan** `python -m pytest tests/test_seed_scenarios.py tests/test_scores.py tests/test_score_clearing.py tests/test_components.py tests/test_finalization.py tests/test_finalization_concurrency.py tests/test_history.py tests/test_dashboard.py tests/test_reports.py tests/test_notifications.py tests/test_mailer.py -q`. Harapkan PASS, coverage case ID lengkap, tidak ada skipped/deleted tests atau suppression baru. Catat seed/sample ID pada failure, tanpa credential.
- [ ] **Step 6: Commit** `test(backend): cover generated positive and negative scenarios`.

## Task 5: CLI, manifest manual, dan bukti preservasi dua database

**Files:** Create `backend/app/seeding/manifest.py`, `__main__.py`, `backend/tests/test_seed_cli.py`, `backend/tests/test_seed_preservation.py`; modify `.gitignore` untuk `.artifacts/` bila belum ditambahkan.

**Interfaces:** Consumes seluruh kontrak sebelumnya; produces `plan/apply/inspect`, manifest JSON dan checklist Markdown di `<output-dir>/<dataset>/`, dengan default root `.artifacts/seeding/`. Tidak mengubah schema/model aplikasi.

- [ ] **Step 1: Tulis tests CLI/manifest yang gagal.** `test_plan_needs_no_database_or_password` memeriksa plan subprocess sukses tanpa DSN/password dan tanpa engine import. `test_apply_rejects_unsafe_configuration_before_connection` memeriksa staging/prod, database `_test`, password kosong, SMTP nyata, output path di luar output-dir lewat dataset invalid, dan seed/fingerprint mismatch. `test_manifest_contains_actionable_cases_without_secrets` memeriksa konfigurasi, IDs, actors, sample counts, UI/API paths, expected results dan placeholder kredensial; password/hash/JWT/DSN tidak muncul. Jangan menyimpan seluruh ORM `__dict__`.
- [ ] **Step 2: Jalankan** `python -m pytest tests/test_seed_cli.py -q`; harapkan FAIL karena CLI/manifest belum tersedia. Perintah child CLI diberi environment sendiri; jangan mengubah `DATABASE_URL` parent pytest.
- [ ] **Step 3: Implementasikan CLI dan lifecycle manifest.** Parse flag profil/samples/rows/reference-time/dataset/output-dir; resolve config dan cetak seed sebelum apply. Gunakan password environment saja. Import/buat engine hanya setelah validasi apply/inspect; `plan` murni. Tulis file dengan temp+atomic replace, manifest planned sebelum DB write, applied setelah commit; persist no secrets. Untuk existing dataset, fingerprint mismatch atau manifest hilang dengan anchor ada harus gagal/read-only sesuai spec, bukan rebuild. `inspect` mengecek missing/changed IDs dan merekonsiliasi status applied dari anchor tanpa memutasi data bisnis.
- [ ] **Step 4: Uji CLI sukses memakai database A disposable.** `test_cli_apply_and_rerun_preserve_manual_dataset` memakai `SEED_PRESERVATION_DATABASE_URL` yang host/instance-nya sama dengan target test, nama DB tepat `manual_fixture`, dan direktori `tmp_path`; child `python -m app.seeding apply` mengarah A. Snapshot seluruh record namespace, edit human simulasi, jalankan rerun dan inspect; assert edit tetap ada, missing records tidak recreate, dan fixture cleanup B tidak menyentuh A. Tambahkan `test_commit_then_manifest_update_failure_is_read_only_recoverable`, `test_anchor_without_manifest_refuses_recreation`, dan `test_new_dataset_name_appends_without_touching_existing`.
- [ ] **Step 5: Buktikan guard seluruh suite.** `test_pytest_cleanup_preserves_other_database` menjalankan child pytest module sentinel pada B dengan env awal `DATABASE_URL=A`, guard memilih B. Child membuat/menghapus fixture miliknya di B; data A sebelum/sesudah identik. Child target sentinel ditempatkan di temporary test file dengan conftest guard yang eksplisit, sehingga pengujian benar-benar melibatkan guard meskipun path berada di temporary directory. Tidak pernah menunjuk DSN `.env.local` untuk eksperimen ini.
- [ ] **Step 6: Jalankan** `python -m pytest tests/test_test_database_guard.py tests/test_seed_generation.py tests/test_seed_persistence.py tests/test_seed_scenarios.py tests/test_seed_cli.py tests/test_seed_preservation.py -q`. Harapkan PASS. Semua artefak berasal dari tmp/disposable resources; setelah pengujian, dataset manual pengguna tetap tidak disentuh.
- [ ] **Step 7: Commit** `feat(backend): expose persistent seed manifests and manual workflow`.

## Task 6: Dokumentasikan workflow human dan lakukan verifikasi akhir

**Files:** Create `docs/seeding.md`; modify `backend/README.md`, `docs/testing.md`, `README.md`, `.env.test.example` untuk mencocokkan kontrak final.

**Interfaces:** Consumes CLI/manifest yang telah diuji. Produces panduan operator yang menjelaskan target DB, lokasi artefak persisten, login dummy, case instructions, dan pemisahan test environment.

- [ ] **Step 1: Tulis walkthrough yang dapat diikuti human.** Dari host/backend atau container interaktif, instal `.[seed]`, gunakan environment lokal yang benar, set `SEED_PASSWORD` tanpa memasukkannya ke file terlacak, jalankan plan/apply/inspect, dan buka URL dari manifest. Untuk container, mount output-dir ke host agar manifest tidak hilang ketika container CLI `--rm`; data DB tetap di named volume layanan. Nyatakan startup seed admin tetap terpisah, tidak ada reset/delete otomatis, rerun mempertahankan edit, dan sampel baru memakai dataset name baru.
- [ ] **Step 2: Dokumentasikan kasus manual dan batas otomatis.** Berikan aktor, target UUID/NIM, langkah UI/API, payload recipe, expected status/state per case; `/users` placeholder memakai API. Untuk invalid payload dan kondisi infrastruktur, jelaskan cara eksekusi yang sesuai. Tulis bahwa notifikasi dataset merupakan simulasi dan bahwa human login tetap tunduk 30/minute. Dokumentasikan dataset `light-load` serta batas total rows, tanpa mengklaim beban concurrency atau hasil performa.
- [ ] **Step 3: Verifikasi contoh perintah dan dependensi.** `python -m app.seeding --help`, `python -m app.seeding plan --dataset review-manual --profile manual --seed 20261105`, dan `python -m app.seeding plan --dataset review-load --profile light-load --seed 20261105` dijalankan tanpa DB write; counts per case dan seluruh tabel memenuhi batas. Parse seluruh PowerShell contoh tanpa mengeksekusinya. Periksa tautan Markdown, nama env dan path mount. Tidak perlu build/lint frontend karena tidak ada perubahan UI.
- [ ] **Step 4: Jalankan pemeriksaan akhir pada container test disposable.** `python scripts/verify_comments.py`, `python -m pip check`, dan `python -m pytest` harus PASS. Jika ada kegagalan existing, investigasi dan laporkan; jangan menghapus kasus atau menurunkan assertions. Catat perintah, seed, versi dependency, jumlah tests dan hasil nyata. Verifikasi preservasi A/B telah lulus; jangan menggunakan database manual pengguna untuk membuktikannya.
- [ ] **Step 5: Review scope/diff** dengan `git diff --check` dan review kode. Periksa tidak ada secrets/artefak seeder masuk Git, tidak ada implicit deletion, startup imports/seeding tidak berubah, dan konfigurasi production tidak ikut dimodifikasi. Pemeriksaan tambahan hanya jika ada perubahan/failure yang membutuhkannya.
- [ ] **Step 6: Commit dokumentasi** `docs: explain persistent dummy data and isolated testing`; laporkan manifest/manual walkthrough yang tersedia kepada human. Pelaksanaan task berhenti setelah acceptance terpenuhi; jangan menjalankan load runner atau membersihkan dataset manual.

## Pemetaan acceptance ke task

| Acceptance | Bukti |
| --- | --- |
| Beberapa contoh pada setiap kasus, jumlah acak berbatas | Task 2: per-case counts, boundaries, catalog/OpenAPI coverage |
| Generator bersama untuk fixtures dan seeder manual | Tasks 2–5: satu SeedPlan dan katalog, dua lifecycle persistence |
| Data manual tidak dihapus/ditimpa tests maupun rerun | Task 1 guard; Tasks 3/5 human-edit snapshots dan proof A/B |
| Case negatif memeriksa penolakan dan state | Task 4 HTTPX dan assertions DB |
| Bisa mereproduksi kegagalan | Tasks 2/4/5 seed/sample/config/versions/reference time |
| Dataset untuk load ringan | Tasks 2/6 preflight profile, hard ceiling dan dokumentasi |
| Tidak mengirim email/task saat seeding | Task 3 fail-on-call; Task 5 env preflight |
| Bisa diikuti human | Tasks 5/6 manifest, checklist dan walkthrough |

## Self-review rencana

- Spec coverage dipetakan ke tasks dan tabel acceptance di atas; tidak ada implementasi atau test database yang dijalankan saat dokumen ini ditulis.
- Kontrak antartugas memberi nama/signature yang sama untuk generator, persistence, manifest, guard, dan executor.
- Review Focus memiliki test pemilik yang eksplisit; builder check desain telah menyelesaikan target CLI disposable dan login limiter.
- Test commands mengarah resource disposable; approval eksekusi diperlukan sebelum mengimplementasikan rencana ini. Rekomendasi metode eksekusi: native berurutan karena generator, persistence, fixtures, dan CLI berbagi kontrak erat; lakukan review independen setelah implementasi.
