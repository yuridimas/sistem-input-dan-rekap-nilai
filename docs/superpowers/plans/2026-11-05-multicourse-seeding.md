# Seeder multi-mata-kuliah Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Perkaya graph data seeder agar setiap dataset memiliki 5–15 mata kuliah, setiap mata kuliah memiliki 2–5 kelas, dan setiap kelas memiliki 5–15 mahasiswa terdaftar.

**Architecture:** Pertahankan generator, manifest, CLI, dan append-only persistence yang sudah ada. RNG lokal berbasis seed menentukan cardinality; katalog skenario memetakan contoh ke resource graph tersebut tanpa menciptakan kelas/roster di luar batas. Semua row hasil graph dan dependensi turunannya masuk ke perhitungan preflight.

**Tech Stack:** Python 3.11+, SQLAlchemy async, PostgreSQL, Polyfactory, Faker `id_ID`, pytest/pytest-asyncio.

**Spec:** `docs/superpowers/specs/2026-11-05-dummy-seeding-design.md`

## Global Constraints

- 5–15 mata kuliah per dataset; 2–5 kelas per mata kuliah; 5–15 mahasiswa terdaftar per kelas.
- Seluruh case positif/negatif tetap menghasilkan variasi sesuai profile; jangan menghapus kasus untuk memenuhi batas row.
- Seeder persisten append-only; jangan reset, truncate, menimpa, atau menghapus dataset yang sudah ada.
- Database pytest harus disposable dan eksplisit; cleanup pytest tidak boleh menyentuh data manual.
- Gunakan RNG lokal reproducible; manifest dan row cap mencakup seluruh relasi.

## Review Focus

- Seed yang sama menghasilkan jumlah dan mapping course/class/student yang sama; seed berbeda tetap menghormati batas.
- Kelas tidak kehilangan/menduplikasi relasi course dan enrollment; tiap roster berada dalam rentang.
- Case mutatif tidak membuat contoh berikutnya bergantung pada side effect sebelumnya; pemetaan resource tetap valid saat graph dibatasi.
- `plan` menghitung seluruh row turunan sebelum transaksi; dataset lama tetap utuh saat `apply` baru.
- Fixture otomatis hanya menggunakan DB disposable yang dipilih eksplisit.

---

### Task 1: Kunci kontrak cardinality dan mapping skenario

**Files:**
- Modify: `backend/app/seeding/scenarios.py`
- Modify: `backend/app/seeding/config.py`
- Test: `backend/tests/test_seed_generation.py`

**Interfaces:**
- `build_plan(config: SeedConfig) -> SeedPlan` tetap menghasilkan resource mapping per case dan sample.
- Manifest menambah ringkasan counts `courses`, `classes`, `students`, dan `enrollments`.

- [x] Tambahkan tests dengan seed tetap yang memeriksa bounds jumlah course, kelas per course, mahasiswa per kelas, dan validitas setiap foreign key.
- [x] Jalankan test seeding terkait dan pastikan gagal pada graph satu course/many classes sekarang.
- [x] Implementasikan pemilihan jumlah 5–15 course, 2–5 kelas/course, dan 5–15 mahasiswa/kelas via RNG lokal yang diturunkan per parent ID.
- [x] Petakan case sample ke resource existing; resource yang berbagi state hanya untuk request nonmutatif. Case state-mutating mendapat target terisolasi dalam batas graph atau dinyatakan automated-only bila tidak dapat direpresentasikan aman.
- [x] Verifikasi tests seeding dan deterministic plan untuk seed yang sama.

### Task 2: Persist graph dan validasi batas row

**Files:**
- Modify: `backend/app/seeding/manifest.py`
- Modify: `backend/app/seeding/planner.py`
- Modify: `backend/app/seeding/persistence.py`
- Test: `backend/tests/test_seed_generation.py`
- Test: `backend/tests/test_seed_persistence.py`

**Interfaces:**
- `plan`/`inspect` expose counts per relasi dan dataset; `apply` menerima rencana yang telah lulus preflight.

- [x] Tambahkan assertions manifest untuk jumlah course/class/student/enrollment dan validitas referensi case.
- [x] Implementasikan persist graph berurutan sesuai FK; preflight jumlah seluruh tabel termasuk score, grade, ranking, notification, audit, dan manifest.
- [x] Pastikan collision atau kegagalan transaksi tidak menghapus row existing dan tidak menandai dataset lama berubah.
- [x] Jalankan test planner, manifest, persistence, dan dry-run `python -m app.seeding plan` dengan dataset name baru.

### Task 3: Tambahkan panduan dan verifikasi append-only

**Files:**
- Modify: `docs/seeding.md`
- Modify: `backend/README.md`
- Test: `backend/tests/seeding/` (tests kontrak yang sudah ada)

- [x] Dokumentasikan cardinality, variasi seed, arti mapping case/resource, dan contoh perintah `plan`/`apply` dengan nama dataset baru.
- [x] Tambahkan assertions agar `apply` dengan nama yang sudah terdaftar tetap melaporkan existing tanpa mengubah data.
- [x] Jalankan semua tests seeding pada PostgreSQL disposable yang dimigrasi; jangan menjalankan pytest pada DB manual.
- [x] Review diff untuk memastikan tidak ada command penghapusan atau perubahan dataset manual yang sudah ada.

**Ruling saat eksekusi:** Repository memakai `build_plan` serta `backend/tests/test_seed_*.py`; `manifest_data` dan append-only persistence sudah menghitung seluruh objek/relasi secara generik, jadi dipertahankan dan diuji daripada ditulis ulang.
