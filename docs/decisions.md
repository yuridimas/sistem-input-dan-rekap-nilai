# Keputusan teknis

Pilihan berikut terlihat pada implementasi saat ini. Konteks historis diarsipkan dalam [spesifikasi desain](superpowers/specs/2026-10-24-sistem-input-rekap-nilai-design.md).

## Lapisan HTTP, bisnis, dan persistence

**Implementasi:** Router mengikat kontrak Pydantic, service menerapkan aturan akses dan penilaian, repository menjalankan operasi SQLAlchemy, dan model/Alembic mendeskripsikan schema. Lihat [`backend/app/`](../backend/app/).

**Trade-off:** Validasi bersama menghindari pengulangan aturan penilaian di handler. Kepemilikan transaksi bervariasi: service penilaian mengoordinasikan commit beberapa tabel, sedangkan sebagian repository CRUD melakukan commit langsung. Periksa batas tersebut sebelum menggabungkan pemanggilan.

## Konsistensi PostgreSQL

**Implementasi:** SQLAlchemy/asyncpg async, foreign key, unique constraint, kolom numerik, dan lock PostgreSQL. Lock kelas mengurutkan perubahan komponen/roster, penyimpanan skor, dan rilis. Ranking memakai window function.

**Trade-off:** Pengujian persistence dan concurrency memerlukan PostgreSQL; SQLite tidak menguji semantik yang khusus untuk dialect ini. Pemeriksa komentar juga melakukan query metadata PostgreSQL.

## Aritmetika eksak

**Implementasi:** [`calculate_final_score`](../backend/app/services/grade.py) mengonversi input Decimal menjadi pecahan eksak, lalu melakukan pembulatan half-up ke dua angka desimal. Input draft yang belum diisi menyumbang nol dengan bobot penuh tetap dipertahankan.

**Trade-off:** Pembagian berulang tidak menggeser batas pembulatan setengah sen. Total draft berguna selama input, tetapi skor yang belum diisi harus tetap dibedakan dari nilai nol sebelum rilis.

## Konfigurasi lengkap dan penguncian rilis

**Implementasi:** Total bobot 100% dengan UTS/UAS; create/replacement batch mendukung perubahan beberapa bobot sekaligus. Finalisasi menghalangi mutasi skor, komponen, dan roster. Komponen yang sudah berskor tidak dapat dihapus atau dikurangi nilai maksimumnya di bawah skor tersimpan.

**Trade-off:** Perhitungan yang dipublikasikan mempertahankan input penilaian. API tidak memiliki alur unfinalize. Metadata deskriptif mata kuliah/kelas/mahasiswa tidak disimpan sebagai snapshot historis immutable yang terpisah.

## Penyimpanan ranking unik

**Implementasi:** [`repositories/ranking.py`](../backend/app/repositories/ranking.py) menyimpan `row_number` dengan urutan skor menurun, NIM menaik, kemudian nama menaik.

**Trade-off:** Total yang sama memperoleh posisi berbeda. Pembacaan mengembalikan ranking saat rilis, bukan menghitung ulang pada setiap request.

## Commit rilis sebelum pengiriman email

**Implementasi:** Grade, ranking, dan record notification di-commit sebelum publikasi Redis. Celery menangani pengiriman, audit persisten mendukung pemulihan, dan dispatch token membedakan percobaan.

**Trade-off:** Kegagalan broker tidak membatalkan grade yang sudah dirilis. HTTP 202 berarti pekerjaan masuk antrean, bukan bukti pengiriman selesai. Record yang belum terkirim dapat di-retry oleh admin. Commit database, enqueue, SMTP, dan pencatatan keberhasilan pengiriman tetap memiliki batas kegagalan terpisah; implementasi ini bukan transactional outbox atau protokol email exactly-once.

## Mock SMTP yang dapat dikonfigurasi

**Implementasi:** `SMTP_HOST` kosong memilih transport logging; SMTP nyata mendukung STARTTLS, SSL, atau transport plain. Lihat [`mailer.py`](../backend/app/services/mailer.py).

**Trade-off:** Development lokal tidak memerlukan server email, tetapi keberhasilan mock tetap menghasilkan status `sent`. Periksa konfigurasi transport saat menafsirkan record audit.

## JWT dan pemeriksaan identitas database

**Implementasi:** bcrypt, JWT access/refresh bertipe, rotasi refresh, dan pencarian akun aktif di database pada request terautentikasi. Axios mengoordinasikan refresh; Zustand menyimpan token dan memuat ulang profil.

**Trade-off:** Deaktivasi/role terkini diperiksa di server. Identifier refresh yang sudah dipakai berada dalam set in-memory per proses, sehingga penolakan replay hilang saat restart dan tidak dibagikan antar-worker API. Penyimpanan token di browser merupakan bagian dari desain saat ini.

## State draft khusus

**Implementasi:** [`draft.ts`](../frontend/src/features/grades/draft.ts) melacak edit/penyimpanan secara terpisah dari snapshot TanStack Query. Lifecycle-nya mencakup tab kelas; navigasi/rilis mengoordinasikan pekerjaan tertunda.

**Trade-off:** Acknowledgement penyimpanan tidak menimpa input yang lebih baru. Perubahan konfigurasi server dapat menjeda editor untuk rekonsiliasi. Edit tertunda tersimpan di memori dan harus disimpan sebelum reload/keluar.

## Tabel data bersama di client

**Implementasi:** [`components/data-table/`](../frontend/src/components/data-table/) membungkus TanStack Table untuk sorting dan pagination. Halaman fitur mengelola pencarian dan filter server. Filter pengguna/notifikasi menunggu **Terapkan**, sedangkan pencarian lokal memproses daftar hasil request. Halaman pengguna mendukung create/update dan deaktivasi akun melalui API admin yang sudah ada.

**Trade-off:** Kontrol tabel yang konsisten tidak memerlukan endpoint pagination baru. Browser memuat seluruh array hasil filter, sehingga ukuran halaman tabel membatasi row yang dirender, bukan jumlah data yang ditransfer server. Kartu ringkasan pengguna menghitung record hasil filter server sebelum pencarian lokal.

## Graph seed append-only yang dapat direproduksi

**Implementasi:** [`app/seeding/`](../backend/app/seeding/) memakai dependensi Polyfactory/Faker opsional dengan versi tetap, RNG berbasis seed, ID UUIDv5, reference time tetap, dan fingerprint konfigurasi. Profile menghasilkan beberapa contoh per case dengan jumlah mata kuliah/kelas/roster berbatas. Apply dataset mengambil advisory lock dan memeriksa anchor sebelum menulis; rerun mempertahankan data dan edit manual yang sudah ada.

**Trade-off:** Skenario baru memerlukan nama dataset baru, bukan reset data milik penguji human. Reproduksi bergantung pada seed, konfigurasi, versi generator, dan versi dependensi. ID serta atribut yang direncanakan bersifat deterministik; hash password dengan salt dan default server tidak dijanjikan identik per byte. Profile `light-load` menyediakan sample data dan target request; repository tidak mencakup load runner atau jaminan performa berdasarkan pengukuran.

## Target database pengujian eksplisit

**Implementasi:** [`tests/support/database_guard.py`](../backend/tests/support/database_guard.py) mewajibkan `TEST_DATABASE_URL`, `TEST_REDIS_URL`, dan `TEST_DATABASE_DISPOSABLE=1`, memvalidasi suffix database PostgreSQL `_test`, serta mengalihkan settings aplikasi sebelum import runtime database/auth/task.

**Trade-off:** Tests tidak dapat diam-diam memakai `.env` developer sebagai fallback. Suffix dan flag eksplisit merupakan deklarasi operator bahwa resource bersifat disposable, bukan bukti server terisolasi; setup Docker yang didokumentasikan menyediakan layanan terpisah. Dataset persisten yang dipakai human berada di luar target pytest.

## Laporan yang dirender server

**Implementasi:** PDF Jinja2/WeasyPrint dan XLSX openpyxl dijalankan dalam thread. Template memakai autoescape, pengambilan resource eksternal PDF diblokir, teks XLSX dinyatakan sebagai data string, dan download memakai `no-store`.

**Trade-off:** Laporan memakai data server yang sudah diotorisasi, tetapi PDF memerlukan library/font native. Dependensi yang tidak tersedia menghasilkan 503. Laporan kelas mewajibkan seluruh hasil pada roster sudah final.

## Profile runtime dan proxy

**Implementasi:** Layanan lokal memakai bind mount/dev server. Deployment menambahkan dependensi migration satu kali, aset statis, volume database khusus, dan Nginx. Project name berbeda memisahkan resource staging/production.

**Trade-off:** Migration lokal dijalankan eksplisit. URL API deployment `/api` ditetapkan saat build frontend, dan TLS memerlukan proxy eksternal. FastAPI saat ini tidak memiliki `root_path` deployment; request schema Swagger melewatkan prefix meskipun `/api/openapi.json` tersedia.

## Flag health

**Implementasi:** [`health.py`](../backend/app/routers/health.py) mengembalikan HTTP sukses dengan boolean `db`/`redis`; probe API deployment memeriksa keduanya.

**Trade-off:** Status HTTP dan `status: ok` saja tidak cukup untuk membuktikan readiness.
