# Desain data dummy untuk pengujian manual dan otomatis

**Status:** Disetujui dan diimplementasikan melalui plan multi-mata-kuliah.
**Tanggal:** 2026-11-05.
**Pilihan yang disetujui pengguna:** Polyfactory + Faker, variasi beberapa contoh untuk setiap kasus positif/negatif, jumlah acak berbatas, dan dataset untuk load test ringan.
**Batas utama dari pengguna:** Dataset seeder dipakai human untuk testing manual dan tidak boleh dihapus oleh pytest atau pengujian otomatis lain. Pytest boleh diperkaya.

## Tujuan dan batas pekerjaan

Sediakan generator data bersama untuk dua konsumen: seeder persisten yang dapat digunakan human lewat aplikasi/API, dan fixture pengujian otomatis di database disposable. Keduanya memakai katalog skenario yang sama agar kasus positif, negatif, dan batas nilai memiliki beberapa variasi yang dapat ditelusuri.

Pekerjaan mencakup CLI seeding, manifest dataset, panduan manual, isolasi pytest, dan penambahan tests yang relevan. Dataset profil `light-load` menyiapkan target/data bagi load runner; implementasi runner concurrency, benchmark/SLA, jutaan baris, UI baru, migrasi schema aplikasi, dan perubahan aturan penilaian berada di luar cakupan.

## Pendekatan yang dipertimbangkan

| Pendekatan | Pertimbangan | Keputusan |
| --- | --- | --- |
| Faker + generator manual | Sedikit dependensi, tetapi konstruksi model dan variasi perlu lebih banyak kode sendiri | Tidak dipilih |
| Polyfactory + Faker + pytest/HTTPX yang sudah ada | Factory SQLAlchemy async dapat dipakai seeder dan fixtures; aturan lintas-record tetap eksplisit | Dipilih pengguna |

Hypothesis dan library load runner tidak menjadi dependensi awal. Kebutuhan variasi berbatas dapat dipenuhi generator bersama dan parametrization pytest yang sudah digunakan repository.

## Dasar implementasi saat ini

- `backend/app/services/seed.py` hanya melakukan bootstrap superadmin; pertahankan tanggung jawab itu.
- Session aplikasi memakai SQLAlchemy async/asyncpg; tests menggunakan PostgreSQL, HTTPX, pytest-asyncio, dan sebagian savepoint.
- Sejumlah tests membuat koneksi sendiri dan menghapus fixture dengan DELETE. Isolasi tidak cukup hanya dengan override dependency `get_db`.
- Bobot harus tepat 100%, mencakup UTS/UAS; skor memakai Decimal, dan finalisasi membentuk ranking serta catatan notifikasi sebelum publish Celery.
- Pembuatan data final oleh seeder tidak boleh memicu pengiriman email/task nyata. History, laporan, dashboard, dan notifikasi membutuhkan keadaan final yang saling konsisten.

## Kontrak wajib

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

## Profil dan keacakan

| Profil | Contoh per case ID | Batas seluruh row yang akan ditambahkan | Penggunaan |
| --- | --- | --- | --- |
| `manual` | Acak 5–15 | 25.000 | Eksplorasi human dan pengujian fungsional |
| `light-load` | Acak 10–30 | 100.000 | Dataset lebih besar untuk load runner ringan |
| Fixture pytest | Acak 5–15 per case ID | 25.000 per dataset fixture | Pengujian otomatis pada database disposable |

Rentang dan batas ini adalah usulan perancang, bukan angka yang sudah dipilih pengguna. CLI mengizinkan `--min-samples`, `--max-samples`, dan `--max-rows` untuk menurunkan batas atau menyesuaikan rentang dengan minimum tetap lima dan hard ceiling 100.000 row per dataset. Preflight menghitung seluruh tabel, termasuk scores, rankings, dan notifications, sebelum membuka transaksi tulis. Bila melewati batas, gagal dengan hitungan jelas; jangan mengurangi jumlah kasus diam-diam.

Seed acak baru dibuat ketika `--seed` tidak diberikan, dan dicetak sebelum mutasi. Generator memakai RNG lokal, child-seed per case ID, UUIDv5/key unik terkontrol, dan reference time tetap default `2026-01-01T00:00:00Z`. Jangan menggunakan clock sekarang, UUID acak tersembunyi, atau global RNG untuk atribut yang dijanjikan reproducible. Nama mahasiswa dapat memakai Faker; NIM, kode mata kuliah, email login, bobot, dan foreign key ditentukan generator domain. Alamat dummy memakai domain `example.test`.

Untuk setiap case, pilih jumlah sample dalam rentang, lalu berikan RNG turunan per sample index agar satu sample dapat direproduksi sendiri. Jumlah tidak harus berbeda untuk setiap pasangan case atau setiap seed; yang dijamin adalah batasnya dan data sample yang berbeda. Payload kredensial/token dalam manifest menggunakan placeholder runtime, bukan password atau token nyata.

## Katalog kasus

Setiap case ID memiliki `operation`, aktor, initial state, payload atau resep variasi, expected HTTP/result assertions, dan petunjuk manual. Katalog memiliki subcase eksplisit, misalnya `score.negative`, `score.over_max`, dan `score.too_precise`; tiap subcase mendapat jumlah contohnya sendiri.

| Kelompok | Kasus positif dan negatif wajib |
| --- | --- |
| Auth dan akun | Login admin/dosen; salah password, akun inactive, kredensial kosong, token absen/invalid, refresh salah jenis; akun CRUD, email duplikat, akses nonadmin |
| Mata kuliah dan kelas | CRUD sah, field wajib/credits invalid, kode duplikat, penugasan dosen sah/tidak sah, resource tidak ada, akses dosen lain |
| Mahasiswa dan roster | Buat/baca, enrollment baru/pakai NIM lama, enrollment duplikat, email invalid/null/omitted, update nonadmin, hapus dengan dependensi, roster kelas final |
| Komponen | Konfigurasi sah bervariasi, total 99.99/100.01, UTS/UAS hilang, bobot/maksimum invalid, null/unknown field, hapus komponen berskor, turunkan maksimum melewati skor, konfigurasi kelas final |
| Skor draft | Save/update, nol/maksimum, null menghapus, omitted mempertahankan, negatif/lebih maksimum, presisi berlebih/nonfinite/bool, komponen/enrollment salah kelas, akses ditolak, audit perubahan |
| Finalisasi/ranking | Kelas lengkap, skor kurang, roster kosong, konfigurasi belum ada, finalisasi ulang, edit setelah final, total 44.99/45.00, tie-break NIM/nama, satu timestamp rilis |
| Read models dan laporan | Dashboard pending/released, history final dan scope dosen, PDF/XLSX sah, draft/kelas belum lengkap ditolak, unduhan tanpa izin |
| Notifikasi | Audit queued/sent/failed, filter, retry unsent, retry sent ditolak, penerima kosong, broker/SMTP gagal dalam test terkontrol |
| Infrastruktur | Health flags dan renderer tidak tersedia melalui penggantian dependency di tests; tidak mematikan layanan manual |

Daftar subcase final dicocokkan dengan seluruh 43 operasi API dan tests yang ada saat implementasi; setiap operasi memiliki mapping coverage atau alasan bahwa case-nya hanya dapat dijalankan otomatis. Ini bukan janji bahwa random generation membuktikan semua kemungkinan input.

Kondisi seperti error renderer, timeout SMTP, broker offline, atau concurrency membutuhkan eksekusi terkontrol. Manifest manual menjelaskan batas tersebut tanpa merusak layanan lokal. Kelas kosong boleh tetap kosong untuk case roster kosong: lima contoh berarti lima target/case samples, bukan memaksa isi roster menjadi lima.

## Factory, graph, dan persistence

Tempatkan fitur dalam `backend/app/seeding/`; jangan mengubah startup seed atau menambah endpoint. Factory membangun atribut model, sedangkan generator skenario menentukan urutan foreign key: users, courses/classes/students, components/enrollments, scores/grades, rankings/notifications.

Bagikan initial state untuk operasi baca dan target yang tidak saling memengaruhi; sediakan resource sendiri untuk aksi yang mengubah state, seperti finalize, delete, clear score, dan notification retry. Beberapa contoh per kasus harus memiliki ID/payload berbeda. Metadata skenario berada dalam manifest, bukan kolom bisnis baru.

Untuk initial state final, gunakan `calculate_final_score` dan urutan ranking repository saat ini, lalu buat audit finalisasi dan catatan notifikasi simulasi dalam transaksi yang sama. Jangan memanggil alur finalisasi yang melakukan commit/publish. Kumpulan final tidak boleh menghasilkan ranking shared, skor tidak lengkap, atau notification timestamp yang bertentangan dengan `release_notified_at`. Aksi finalisasi nyata tetap diuji melalui service/API dalam tests.

## CLI dan manifest persisten

Entry point: `python -m app.seeding`. Subcommand awal hanya `plan`, `apply`, dan `inspect`.

```text
python -m app.seeding plan --dataset manual-v1 --profile manual --seed 20261105
python -m app.seeding apply --dataset manual-v1 --profile manual --seed 20261105
python -m app.seeding inspect --dataset manual-v1
```

`plan` tidak terhubung ke database dan tidak memerlukan password. `apply` memerlukan `SEED_PASSWORD` dari environment untuk login akun dummy, menolak `DEPLOYMENT_ENV=staging/prod`, menolak nama database berakhiran `_test`, dan menolak SMTP nyata yang aktif. `inspect` hanya membaca manifest dan record terkait. Semua proses menggunakan environment aplikasi yang dipilih operator; URL/password tidak dicetak dalam laporan.

Simpan artefak dalam `.artifacts/seeding/<dataset>/` pada root repository, diabaikan Git. `--output-dir` mengizinkan mount direktori host ketika memakai container. Tulis manifest rencana secara atomik sebelum insert. Isi manifest: configuration fingerprint, seed/reference time/versions, namespace, IDs/key record, actor email/role, case IDs dan sample counts, payload/expected result, URL UI/API, status simulasi, serta waktu apply. Jangan simpan password, password hash, JWT, atau URL berkredensial.

Anchor dataset adalah UUIDv5 satu akun dummy yang berasal dari dataset namespace. Sebelum insert, periksa manifest dan anchor tanpa mengubah record. Dataset/anchor yang sudah ada menghasilkan ringkasan read-only; konfigurasi berbeda untuk nama yang sama menghasilkan error tanpa mutasi. Manifest hilang tetapi anchor ada menghasilkan error pemulihan tanpa mencoba recreate. Jika transaksi gagal sebelum anchor commit, manifest `planned` dapat dipakai mengulang rencana yang sama. Jika commit berhasil tetapi update manifest gagal, inspect merekonsiliasi status terhadap anchor tanpa menulis ulang data bisnis. Benturan dari proses seeding bersamaan dilaporkan sebagai konflik, tanpa cleanup data proses lain.

`inspect` melaporkan record yang hilang/berubah akibat aksi human sebagai hasil observasi; tidak otomatis memperbaikinya. Manifest berisi checklist awal dan peringatan bahwa aksi tulis human dapat mengubah prasyarat kasus berikutnya. Menjalankan ulang apply tidak mengembalikan initial state; buat nama dataset baru bila ingin sampel segar.

## Isolasi pengujian otomatis

Tambahkan guard pada `backend/tests/conftest.py` sebelum import module aplikasi dari test collection. Wajibkan `TEST_DATABASE_URL`, `TEST_REDIS_URL`, dan `TEST_DATABASE_DISPOSABLE=1`; nama database harus berakhiran `_test`. Set `DATABASE_URL` dan `REDIS_URL` untuk seluruh proses pytest dari nilai test tersebut sebelum engine/settings/task diimpor. Kosongkan SMTP host. Tidak ada fallback ke `.env`, database `grades`, atau URL manual. Konfigurasi ini adalah kontrak eksplisit bahwa operator menyediakan resource disposable, bukan deteksi otomatis keamanan suatu server.

Jika runtime `app.database`, `app.celery_app`, atau `app.services.auth` sudah dimuat sebelum guard, gagal sebelum koleksi, karena module tersebut bisa menyimpan engine/URL/settings lama. Setelah validasi dan penggantian environment, bersihkan cache `get_settings` sebelum import runtime pertama. Buktikan cache settings yang sempat dibaca tidak mengembalikan konfigurasi manual setelah guard.

Bootstrap akun yang dibutuhkan tests tetap dilakukan eksplisit pada database test. Simpan compatibility shim HTTPX yang ada. Test subprocess untuk guard tidak menghubungi database dan membuktikan konfigurasi yang kurang ditolak sebelum koleksi/import engine. Pengujian fixture, API, concurrency, dan background task memakai resource test yang sama; worker manual tidak dilibatkan.

Persistence core diuji langsung dengan session database `_test`. Pengujian sukses CLI `apply` dan preservasi menggunakan database disposable kedua bernama `manual_fixture` di container khusus pengujian, melalui subprocess CLI dengan environment eksplisit; pytest tetap bertarget database B. Tidak ditambahkan flag bypass ke CLI seeder. Test harness harus memastikan host/instance A sama dengan resource disposable yang dibuatnya dan nama A tepat `manual_fixture` sebelum menulis.

Kasus login fungsional baru menonaktifkan limiter hanya dalam scope fixture pengujian tersebut dan memulihkannya setelah test. Kasus rate limit tersendiri mengaktifkan/reset limiter dan memeriksa respons 429 setelah batas 30/minute dari satu alamat. Walkthrough manual tetap menghormati limiter aplikasi: 429 akibat pengulangan cepat memerlukan menunggu jendela pembatasan, bukan mengubah dataset atau menonaktifkan pembatas di aplikasi.

Buktikan preservasi dengan dua database disposable: A berisi dataset yang mewakili seeder human, B untuk pytest. Jalankan pengujian pada B walaupun environment awal `DATABASE_URL` mengarah A. Bandingkan fingerprint data A sebelum/sesudah, termasuk edit human simulasi. Jangan memakai database manual pengguna sebagai bahan uji destructive atau cleanup.

## Strategi pengujian dan hasil selesai

- Unit tests: repeatability data plan, rentang jumlah, coverage per case ID, mandatory boundaries, exact Decimal weights, graph IDs, preflight limits, payload negatif, dan manifest tanpa secrets.
- PostgreSQL disposable: satu transaksi apply, rollback saat konflik, rerun mempertahankan edit human, no publish/SMTP, konsistensi graph final, dan pemisahan A/B.
- HTTPX: jalankan case samples berlabel lewat endpoint dengan assertions atas status, detail relevan, dan state DB. Kasus negatif tidak hanya memeriksa HTTP gagal; periksa bahwa mutasi yang ditolak tidak terjadi.
- Pertahankan tests batas dan concurrency yang ada; tambah variasi terarah tanpa mengganti seluruh suite dengan loops acak.
- Dokumentasikan manual walkthrough memakai manifest serta cara membuat profil `light-load`. Tidak ada klaim performa tanpa load runner dan pengukuran.

Selesai ketika seluruh case ID memiliki beberapa sampel, manifest bisa dipakai human, data manual tetap ada setelah tests dan rerun, suite terkait lulus pada database disposable, dan panduan menyebutkan environment/target yang dipakai setiap perintah.

## Hasil builder check

Review fresh-context meminta penjelasan target database untuk pengujian CLI dan isolasi login limiter. Keduanya diselesaikan di atas sebagai keputusan perancang. Angka profil, nama CLI/artefak, reference time, dan detail guard tetap usulan teknis untuk ditinjau pengguna bersama rencana; tidak ada implementasi yang dijalankan pada tahap perencanaan.

## Referensi resmi

- [Polyfactory SQLAlchemy async dan kontrol flush/commit](https://polyfactory.litestar.dev/latest/usage/library_factories/sqlalchemy_factory.html).
- [Polyfactory RNG dan Faker instance](https://polyfactory.litestar.dev/latest/usage/configuration.html).
- [Faker: seed dan batas reproduksibilitas versi](https://faker.readthedocs.io/en/stable/index.html).
- [Faker locale Indonesia](https://faker.readthedocs.io/en/stable/locales/id_ID.html).
