# Data dummy persisten

Seed CLI menambah dataset yang tetap tersedia untuk pengujian human. Command yang tersedia adalah `plan`, `apply`, dan `inspect`; anchor existing dibaca tanpa mereset record atau menimpa edit manual. Gunakan nama dataset baru jika membutuhkan initial state yang segar.

## Instalasi dan perencanaan

Dari **`backend/` menggunakan PowerShell**, pasang dependensi opsional lalu buat plan tanpa akses database:

```powershell
python -m pip install -e ".[seed]"
python -m app.seeding plan --dataset review-manual-v3 --profile manual --seed 20261105
python -m app.seeding plan --dataset review-light-v3 --profile light-load --seed 20261105
```

Artefak berada di `.artifacts/seeding/<dataset>/manifest.json` relatif terhadap working directory proses. Jika dijalankan dari `backend/`, lokasi host menjadi `backend/.artifacts/seeding/`. `--output-dir` memilih root artefak lain.

| Profile | Sample per kasus hasil generator | Default batas seluruh row |
| --- | --- | --- |
| `manual` | Acak 5–15 | 25.000 |
| `light-load` | Acak 10–30 | 100.000 |

Generator versi 3 membangun graph dengan batas 5–15 mata kuliah, 2–5 kelas per mata kuliah, serta 5–15 mahasiswa terdaftar per kelas. Kapasitas yang diperlukan katalog kasus membatasi pemilihan jumlah acak tersebut. Batas row mencakup skor, nilai akhir, ranking, dan record notifikasi; jika terlampaui, perencanaan berhenti sebelum menulis database. Profile `light-load` menyediakan data dan target request tanpa menjalankan benchmark atau concurrency scheduler.

Reproduksi memerlukan nama dataset, seed, profile/rentang sample, reference time, versi generator, serta versi dependensi yang sama. Jika `--seed` dihilangkan, seed hasil generator muncul pada output; gunakan kembali untuk `apply` dan `inspect`. Default reference time adalah `2026-01-01T00:00:00Z`. Hash password bersalt dan default database tidak dijanjikan identik byte demi byte. Pertahankan custom sample range di sekitar rentang profile yang didukung agar sesuai kapasitas kelas berbatas.

## Meninjau pemetaan

Objek `counts` pada manifest merangkum row per tabel, termasuk `courses`, `classes`, `students`, dan `enrollments`. Setiap sample memiliki case/sample ID, actor key, method/path, payload, expected HTTP status, serta ID target course/class/student/enrollment/component. Katalog juga menunjukkan operasi `automated-only` dan file pytest terkait.

Sample manual dalam satu kasus memakai target mahasiswa berbeda; setiap sample finalisasi sukses memiliki kelas terpisah. Pada `light-load`, sample dapat memakai ulang target roster setelah seluruh 15 mahasiswa kelas terpakai. Request tulis mengubah prasyarat sehingga manifest perlu diperiksa sebelum eksekusi; gunakan nama dataset baru untuk skenario mutasi yang segar. Payload invalid merupakan instruksi API, bukan record yang dipaksakan melanggar constraint database.

`actor_accounts` mencantumkan email superadmin, dosen, dan dosen pembanding. Ketiganya merupakan aktor dengan dua role aplikasi: `superadmin` dan `lecturer`. Semua memakai `SEED_PASSWORD` yang diberikan pada apply pertama. Manifest menyimpan placeholder, sedangkan database menyimpan hash password. Superadmin dapat menemukan akun melalui **Pengguna** (`/users`). Login demo tetap mengikuti login limiter aplikasi.

## Apply dan inspect di host

Pilih database development manual yang dimaksud melalui `DATABASE_URL` atau file environment backend, kosongkan SMTP, dan tentukan `APP_ENV=development` atau `local` secara eksplisit. CLI menolak nama database berakhiran `_test`, system database, SMTP aktif, dan environment di luar allowlist. `APP_ENV=test` khusus untuk database `manual_fixture`.

Dari **`backend/` menggunakan PowerShell**:

```powershell
$seedCredential = Get-Credential -UserName 'seed-demo' -Message 'Password untuk seluruh akun demo baru'
$env:SEED_PASSWORD = $seedCredential.GetNetworkCredential().Password
$env:APP_ENV = 'development'
$env:SMTP_HOST = ''
python -m app.seeding apply --dataset review-manual-v3 --profile manual --seed 20261105
python -m app.seeding inspect --dataset review-manual-v3 --profile manual --seed 20261105
Remove-Item Env:SEED_PASSWORD
```

`apply` memerlukan password meskipun dataset sudah ada. Password berbeda saat apply ulang tidak mengubah akun tersimpan. Jika manifest mencatat dataset yang sudah di-apply tetapi ada row hilang, `apply` menolak membuatnya kembali. Konflik konfigurasi/fingerprint memerlukan nama dataset baru.

`inspect` membaca ID yang diharapkan dan melaporkan jumlah row hilang tanpa memperbaiki data. Pemeriksaan hanya mencakup keberadaan, bukan membandingkan setiap field yang diubah human. Command juga menulis observasi ke manifest lokal, sehingga direktori artefak harus tetap dapat ditulis.

## Menjalankan melalui Docker

Backend Compose lokal memasang `./backend` pada `/app`. Image runtime memasang package backend dasar; pasang extra `seed` pada container yang sedang berjalan. Ulangi instalasi setelah recreate container jika extra tersebut tidak lagi tersedia.

Dari **root repository menggunakan PowerShell**, dengan stack lokal berjalan dan `.env.local` memilih database manual yang dimaksud:

```powershell
docker compose --env-file .env.local --profile local exec -T backend python -m pip install -e ".[seed]"
docker compose --env-file .env.local --profile local exec -T backend python -m app.seeding plan --dataset docker-review-v3 --profile manual --seed 20261105 --output-dir /app/.artifacts/seeding

$seedCredential = Get-Credential -UserName 'seed-demo' -Message 'Password untuk seluruh akun demo baru'
$env:SEED_PASSWORD = $seedCredential.GetNetworkCredential().Password
docker compose --env-file .env.local --profile local exec -T -e APP_ENV=local -e SMTP_HOST= -e SEED_PASSWORD backend python -m app.seeding apply --dataset docker-review-v3 --profile manual --seed 20261105 --output-dir /app/.artifacts/seeding
Remove-Item Env:SEED_PASSWORD

docker compose --env-file .env.local --profile local exec -T -e APP_ENV=local -e SMTP_HOST= backend python -m app.seeding inspect --dataset docker-review-v3 --profile manual --seed 20261105 --output-dir /app/.artifacts/seeding
```

Bind mount mempertahankan manifest pada `backend/.artifacts/seeding/docker-review-v3/manifest.json`. Container one-off lain memerlukan output mount persisten sendiri. Gunakan direktori output dan argumen generator yang sama pada ketiga command.

Konstruksi seed tidak memublikasikan task Celery atau menghubungi SMTP. Record notifikasi merupakan simulasi state sent/failed; menjalankan request API manifest seperti finalisasi/retry dapat mengantrekan pekerjaan nyata melalui aplikasi yang berjalan.

## Memisahkan data manual dari pytest

Pytest mewajibkan `TEST_DATABASE_URL`, `TEST_REDIS_URL`, dan `TEST_DATABASE_DISPOSABLE=1` secara eksplisit. Nama database harus berakhiran `_test`. Startup guard mengalihkan koneksi aplikasi sebelum import module runtime, dan fixture seed hanya menambah data pada target disposable tersebut. Dataset human harus tetap berada pada target development manual. Ikuti [pengujian](testing.md) atau [panduan backend](../backend/README.md#menjalankan-tests-pada-database-disposable) untuk penyediaan resource dan command.
