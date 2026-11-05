# Data dummy persisten

Seeder menghasilkan dataset tambahan yang tetap tersedia untuk uji manual. Ia tidak menyediakan reset, truncate, atau penghapusan data. Setiap nama dataset hanya ditambahkan sekali; jika anchor sudah ada, `apply` melaporkan `existing` dan tidak mengubah data. Untuk percobaan baru gunakan nama dataset baru.

## Instalasi dan perencanaan

Dari `backend/`, instal dependensi seeder dan buat rencana tanpa koneksi database:

```powershell
python -m pip install -e ".[seed]"
python -m app.seeding plan --dataset review-manual --profile manual --seed 20261105
python -m app.seeding plan --dataset review-light --profile light-load --seed 20261105
```

Manifest dan checklist JSON disimpan di `.artifacts/seeding/<dataset>/manifest.json`. `manual` membuat 5–15 sample per case (dengan batas 25.000 row), sementara `light-load` membuat 10–30 sample per case (maksimum 100.000 row). Seed, nama dataset, dan versi generator yang sama mereproduksi rencana yang sama.

## Simpan dan periksa dataset

Konfigurasikan `DATABASE_URL` dan Redis ke environment development yang memang ditujukan untuk pemeriksaan manual. Database harus bernama terpisah, bukan database test, dan SMTP harus nonaktif. Isi password akun demo hanya di environment shell:

```powershell
$env:SEED_PASSWORD = "password-demo-yang-kuat"
$env:APP_ENV = "development"
python -m app.seeding apply --dataset review-manual --profile manual --seed 20261105
python -m app.seeding inspect --dataset review-manual --profile manual --seed 20261105
```

`inspect` hanya membaca database dan menampilkan jumlah ID row yang hilang. Jika manifest sebelumnya menunjukkan dataset sudah di-apply tetapi row hilang, `apply` menolak membuat ulang data tersebut.

Seeder tidak mengirim email atau task Celery. Password disimpan sebagai hash pada akun demo dan tidak masuk ke manifest. Jalankan CLI dari container hanya jika output `.artifacts/seeding` dimount ke host agar manifest tetap tersedia.

Setiap case mempunyai beberapa ID sample, aktor, resource IDs/NIM, method/path, payload, dan expected HTTP status pada manifest. Katalog juga menunjukkan operasi `automated-only` dan file pytest terkait untuk alur CRUD yang tidak diberi request sample manual. Akun superadmin, dosen, dan dosen pembanding memakai email pada `actor_accounts`; semuanya memakai password yang sama dengan `SEED_PASSWORD` saat `apply`. Jalankan positive samples untuk melihat respons dan data tersimpan; jalankan negative samples melalui API/UI untuk memeriksa validasi atau otorisasi. Payload invalid adalah instruksi request dan tidak dimasukkan sebagai record database. Akun demo tetap mengikuti batas login aplikasi.

pytest menggunakan `TEST_DATABASE_URL` yang secara eksplisit menunjuk database disposable berakhiran `_test`, `TEST_REDIS_URL`, dan `TEST_DATABASE_DISPOSABLE=1`. Guard mengalihkan koneksi sebelum import aplikasi; fixture pytest tidak menghapus data di database development. Lihat [panduan backend](../backend/README.md) untuk menjalankan suite disposable.
