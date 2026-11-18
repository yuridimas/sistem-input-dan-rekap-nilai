# Referensi API

## Base URL dan kontrak

| Runtime | Base API | Schema |
| --- | --- | --- |
| Docker lokal | `http://localhost:18000` | `/openapi.json` |
| Uvicorn di host | `http://localhost:8000` | `/openapi.json` |
| Deployment | Origin frontend ditambah `/api` | `/api/openapi.json` pada origin tersebut |

Path berikut relatif terhadap base API. Parameter path UUID mengidentifikasi record database. Format JSON dipakai selain untuk download laporan. Response DELETE yang berhasil tidak memiliki body. Nilai Decimal pada response diserialisasi sebagai string; client perlu menerima string desimal tanpa mengasumsikannya sebagai angka JSON.

FastAPI menyediakan Swagger langsung pada `/docs` dan ReDoc pada `/redoc`. Swagger deployment saat ini meminta path schema tanpa prefix; gunakan `/api/openapi.json` atau Swagger API langsung. Lihat [deployment](deployment.md#reverse-proxy-dan-tls).

Daftar berikut mencakup seluruh 43 operasi aplikasi yang didaftarkan oleh [`main.py`](../backend/app/main.py). Nama kontrak sesuai dengan [`app/schemas/`](../backend/app/schemas/) dan komponen OpenAPI. Login dan refresh membaca `Request` secara manual, sehingga body yang diterima dideskripsikan di sini meskipun OpenAPI tidak mendeklarasikan request body tersebut.

## Autentikasi

`POST /auth/login` menerima JSON `{ "email": "...", "password": "..." }`; `username` merupakan alias email. Endpoint ini juga mendukung parsing form. Contoh berikut memakai request JSON. Login dibatasi 30 percobaan/menit per alamat remote.

`POST /auth/refresh` menerima JSON `{ "refresh_token": "..." }`, dengan `token` sebagai alias. Endpoint ini juga mendukung query parameter, input form, dan body token mentah. Kirim refresh token dalam body JSON. Kedua operasi mengembalikan `TokenResponse`: `access_token`, `refresh_token`, dan `token_type: "bearer"`.

Gunakan `Authorization: Bearer <access_token>` untuk operasi terlindungi. Refresh merotasi kedua token; waktu kedaluwarsa default adalah 15 menit untuk access dan tujuh hari untuk refresh. Daftar refresh yang sudah dipakai berlaku per proses, hilang saat restart, dan tidak dibagikan antar-worker API. Akun nonaktif ditolak meskipun tokennya belum kedaluwarsa.

## Persiapan contoh PowerShell

Jalankan pada instance development/test yang sudah terpasang. Login dengan akun yang dikonfigurasi:

```powershell
$apiBase = 'http://localhost:18000'
$credential = Get-Credential -Message 'Login aplikasi'
$loginPayload = @{
  email = $credential.UserName
  password = $credential.GetNetworkCredential().Password
}
$tokens = Invoke-RestMethod -Method Post -Uri "$apiBase/auth/login" `
  -ContentType 'application/json' -Body ($loginPayload | ConvertTo-Json)

function Invoke-GradeApi {
  param([string]$Method, [string]$Path, $Body)
  $request = @{
    Method = $Method
    Uri = "$apiBase$Path"
    Headers = @{ Authorization = "Bearer $($tokens.access_token)" }
  }
  if ($PSBoundParameters.ContainsKey('Body')) {
    $request.ContentType = 'application/json'
    $request.Body = ConvertTo-Json -InputObject $Body -Depth 10
  }
  Invoke-RestMethod @request
}
```

Tabel memakai helper ini, variabel payload di bawah, dan ID yang dikembalikan instance (`$userId`, `$courseId`, `$classId`, `$studentId`, `$enrollmentId`, `$componentId`, `$notificationId`). Setiap perintah pada tabel menggambarkan satu operasi; seluruh mutasi tidak dimaksudkan untuk dijalankan berurutan sebagai satu script. Contoh khusus admin memerlukan token superadmin.

## Daftar operasi

### Identitas dan health

| Method dan path | Input | Sukses | Tujuan dan contoh |
| --- | --- | --- | --- |
| `GET /health` | Tidak ada; publik | 200: `{status, db, redis}` | Flag dependensi: `Invoke-RestMethod "$apiBase/health"` |
| `POST /auth/login` | Email/username dan password | 200: `TokenResponse` | Contoh login di atas |
| `POST /auth/refresh` | Refresh token | 200: `TokenResponse` | `$tokens = Invoke-GradeApi POST '/auth/refresh' @{refresh_token=$tokens.refresh_token}` |
| `GET /auth/me` | Bearer token | 200: `UserResponse` | `Invoke-GradeApi GET '/auth/me'` |

Health mengembalikan `status: ok` dan HTTP 200 meskipun dependensi gagal; pastikan kedua boolean bernilai true.

### Akun: khusus superadmin

| Method dan path | Input | Sukses | Tujuan dan contoh |
| --- | --- | --- | --- |
| `POST /admin/users` | `UserCreate` | 201: `UserRead` | Buat akun: `Invoke-GradeApi POST '/admin/users' $userCreate` |
| `GET /admin/users` | Query opsional `role`, `is_active` | 200: `UserRead[]` | `Invoke-GradeApi GET '/admin/users?role=lecturer&is_active=true'` |
| `GET /admin/users/{user_id}` | UUID | 200: `UserRead` | `Invoke-GradeApi GET "/admin/users/$userId"` |
| `PATCH /admin/users/{user_id}` | `UserUpdate` | 200: `UserRead` | `Invoke-GradeApi PATCH "/admin/users/$userId" $userUpdate` |
| `DELETE /admin/users/{user_id}` | UUID | 204 | Nonaktifkan dengan mempertahankan relasi historis: `Invoke-GradeApi DELETE "/admin/users/$userId"` |

Halaman **Pengguna** (`/users`) untuk superadmin memakai API ini untuk membuat akun, memperbarui profil/role/status/password, dan menonaktifkan akun. Filter daftar dikirim setelah **Terapkan**; pencarian nama/email, sorting, dan pagination berjalan di browser pada array hasil request. Kontrak response tidak pernah menampilkan hash password.

### Mata kuliah

| Method dan path | Input | Sukses | Tujuan dan contoh |
| --- | --- | --- | --- |
| `POST /courses` | `CourseCreate` | 201: `CourseRead` | Pembuat adalah pengguna saat ini: `Invoke-GradeApi POST '/courses' $courseCreate` |
| `GET /courses` | Tidak ada | 200: `CourseRead[]` | Admin: semua; dosen: mata kuliah yang dibuat atau diampu. `Invoke-GradeApi GET '/courses'` |
| `GET /courses/{course_id}` | UUID | 200: `CourseRead` | Pembuat/admin/dosen pengampu: `Invoke-GradeApi GET "/courses/$courseId"` |
| `PATCH /courses/{course_id}` | `CourseUpdate` | 200: `CourseRead` | Pembuat/admin: `Invoke-GradeApi PATCH "/courses/$courseId" $courseUpdate` |
| `DELETE /courses/{course_id}` | UUID | 204 | Pembuat/admin, mengikuti batasan dependensi: `Invoke-GradeApi DELETE "/courses/$courseId"` |

### Kelas dan roster

Kedua role dapat memanggil operasi ini. Akses ke kelas yang sudah ada memerlukan dosen pengampu atau superadmin.

| Method dan path | Input | Sukses | Tujuan dan contoh |
| --- | --- | --- | --- |
| `POST /classes` | `ClassCreate` | 201: `ClassRead` | `Invoke-GradeApi POST '/classes' $classCreate` |
| `GET /classes` | Tidak ada | 200: `ClassRead[]` | Kelas yang dapat diakses: `Invoke-GradeApi GET '/classes'` |
| `GET /classes/{class_id}` | UUID | 200: `ClassRead` | `Invoke-GradeApi GET "/classes/$classId"` |
| `PATCH /classes/{class_id}` | `ClassUpdate` | 200: `ClassRead` | `Invoke-GradeApi PATCH "/classes/$classId" $classUpdate` |
| `DELETE /classes/{class_id}` | UUID | 204 | Dependensi dapat menghalangi penghapusan: `Invoke-GradeApi DELETE "/classes/$classId"` |
| `POST /classes/{class_id}/enrollments` | `EnrollmentCreate` | 201: `RosterEntryRead` | Pakai ulang/buat profil berdasarkan NIM: `Invoke-GradeApi POST "/classes/$classId/enrollments" $enrollmentCreate` |
| `GET /classes/{class_id}/roster` | UUID | 200: `RosterEntryRead[]` | `Invoke-GradeApi GET "/classes/$classId/roster"` |
| `DELETE /classes/{class_id}/enrollments/{enrollment_id}` | UUID kelas/enrollment | 204 | `Invoke-GradeApi DELETE "/classes/$classId/enrollments/$enrollmentId"` |

Superadmin wajib memasok `lecturer_id` dosen aktif saat membuat kelas. Dosen boleh tidak mengirimkannya dan otomatis ditugaskan ke dirinya sendiri; dosen tidak dapat menugaskan dosen lain. Mutasi roster diblokir setelah rilis. Data penilaian yang bergantung pada enrollment juga dapat menghalangi penghapusannya.

### Direktori mahasiswa

| Method dan path | Input | Sukses | Tujuan dan contoh |
| --- | --- | --- | --- |
| `POST /students` | `StudentCreate` | 201: `StudentRead` | Kedua role: `Invoke-GradeApi POST '/students' $studentCreate` |
| `GET /students` | Tidak ada | 200: `StudentRead[]` | Kedua role: `Invoke-GradeApi GET '/students'` |
| `GET /students/{student_id}` | UUID | 200: `StudentRead` | Kedua role: `Invoke-GradeApi GET "/students/$studentId"` |
| `PATCH /students/{student_id}` | `StudentUpdate` | 200: `StudentRead` | Khusus admin: `Invoke-GradeApi PATCH "/students/$studentId" $studentUpdate` |
| `DELETE /students/{student_id}` | UUID | 204 | Khusus admin; profil yang terdaftar pada kelas menghasilkan conflict: `Invoke-GradeApi DELETE "/students/$studentId"` |

### Komponen, skor, dan rilis

Operasi ini memerlukan akses dosen pengampu atau superadmin. Riwayat mahasiswa dibatasi pada hasil rilis yang dapat diakses pemanggil.

| Method dan path | Input | Sukses | Tujuan dan contoh |
| --- | --- | --- | --- |
| `GET /classes/{class_id}/components` | UUID | 200: `ComponentRead[]` | `Invoke-GradeApi GET "/classes/$classId/components"` |
| `POST /classes/{class_id}/components` | `ComponentCreate[]` tidak kosong | 201: `ComponentRead[]` | Batch atomik: `Invoke-GradeApi POST "/classes/$classId/components" $componentCreate` |
| `PUT /classes/{class_id}/components` | `ComponentWrite[]` tidak kosong | 200: `ComponentRead[]` | Konfigurasi lengkap: `Invoke-GradeApi PUT "/classes/$classId/components" $componentWrite` |
| `PATCH /components/{component_id}` | `ComponentUpdate` | 200: `ComponentRead` | `Invoke-GradeApi PATCH "/components/$componentId" $componentUpdate` |
| `DELETE /components/{component_id}` | UUID | 204 | Konfigurasi yang tersisa harus valid: `Invoke-GradeApi DELETE "/components/$componentId"` |
| `GET /classes/{class_id}/grades` | UUID | 200: `ClassGradesRead` | Grid roster lengkap: `Invoke-GradeApi GET "/classes/$classId/grades"` |
| `PUT /enrollments/{enrollment_id}/scores` | Map UUID ke skor/null yang tidak kosong | 200: `GradeRead` | Update parsial: `Invoke-GradeApi PUT "/enrollments/$enrollmentId/scores" $scorePatch` |
| `POST /classes/{class_id}/finalize` | Tanpa body | 202: `FinalizeRead` | Commit rilis, lalu enqueue: `Invoke-GradeApi POST "/classes/$classId/finalize"` |
| `GET /classes/{class_id}/ranking` | UUID | 200: `RankingRead[]` | Ranking tersimpan: `Invoke-GradeApi GET "/classes/$classId/ranking"` |
| `GET /students/{student_id}/history` | UUID mahasiswa | 200: `HistoryRead[]` | Riwayat rilis: `Invoke-GradeApi GET "/students/$studentId/history"` |

Total bobot harus 100% dan mencakup UTS/UAS. PUT konfigurasi mempertahankan ID yang sudah ada atau tidak mengirim ID untuk komponen baru. PATCH/DELETE individual juga harus menyisakan konfigurasi lengkap yang valid. Grade final menghalangi perubahan skor, roster, dan komponen. Komponen yang sudah berskor tidak dapat dihapus; nilai maksimumnya tidak dapat diturunkan di bawah skor tersimpan.

Untuk skor, jangan kirim ID agar input dipertahankan, kirim `null` untuk menghapus, dan kirim nol untuk nilai nol yang nyata. Skor mengizinkan maksimal dua angka desimal dan tidak dapat melebihi nilai maksimum komponen. Finalisasi memerlukan roster yang tidak kosong dan seluruh skor lengkap. Ranking seri memperoleh posisi berbeda dengan urutan NIM/nama.

### Dashboard dan audit notifikasi

| Method dan path | Input | Sukses | Tujuan dan contoh |
| --- | --- | --- | --- |
| `GET /dashboard/summary` | Tidak ada | 200: `DashboardSummaryRead` | Kedua role, sesuai cakupan akses: `Invoke-GradeApi GET '/dashboard/summary'` |
| `GET /admin/notifications` | Opsional `status=queued`, `sent`, atau `failed` | 200: `NotificationRead[]` | Khusus admin: `Invoke-GradeApi GET '/admin/notifications?status=failed'` |
| `POST /admin/notifications/{notification_id}/retry` | Tanpa body | 202: `NotificationRead` | Retry admin untuk record yang belum terkirim: `Invoke-GradeApi POST "/admin/notifications/$notificationId/retry"` |

Retry menolak record sent, memperbarui email mahasiswa dari profil, dan menyiapkan generasi dispatch baru. HTTP 202 tidak mengonfirmasi pengiriman selesai.

### Download

Operasi ini memerlukan akses dosen pengampu atau superadmin. Kirim header bearer dan simpan konten biner ke file.

```powershell
$downloadHeaders = @{Authorization = "Bearer $($tokens.access_token)"}
```

| Method dan path | Input | Sukses | Contoh |
| --- | --- | --- | --- |
| `GET /reports/student/{enrollment_id}/pdf` | UUID enrollment final | 200: attachment PDF | `Invoke-WebRequest "$apiBase/reports/student/$enrollmentId/pdf" -Headers $downloadHeaders -OutFile student.pdf` |
| `GET /reports/class/{class_id}/pdf` | UUID kelas yang seluruh nilainya final | 200: attachment PDF | `Invoke-WebRequest "$apiBase/reports/class/$classId/pdf" -Headers $downloadHeaders -OutFile class.pdf` |
| `GET /reports/class/{class_id}/xlsx` | UUID kelas yang seluruh nilainya final | 200: attachment XLSX | `Invoke-WebRequest "$apiBase/reports/class/$classId/xlsx" -Headers $downloadHeaders -OutFile class.xlsx` |

PDF memakai `application/pdf`; XLSX memakai `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`. Download mengatur `Content-Disposition: attachment` dan `Cache-Control: no-store`. Dependensi renderer yang tidak tersedia menghasilkan 503. Buat ulang header download jika token berotasi.

## Contoh payload

Gunakan UUID aktual dari server. Contoh berikut mendefinisikan payload; kirim payload terkait memakai daftar operasi di atas. Untuk password dosen baru, ambil credential alih-alih menyimpannya dalam dokumen:

```powershell
$newLecturer = Get-Credential -Message 'Email dan password dosen baru'
$userCreate = @{
  email = $newLecturer.UserName
  password = $newLecturer.GetNetworkCredential().Password
  full_name = 'Example Lecturer'
  role = 'lecturer'
}
$userUpdate = @{full_name = 'Updated Lecturer'; is_active = $true}
$courseCreate = @{code='IF101'; name='Algorithms'; credits=3; semester='Ganjil'}
$courseUpdate = @{name='Introduction to Algorithms'}
# Untuk pembuatan oleh admin, gunakan ID dosen dari /admin/users.
$classCreate = @{course_id=$courseId; section='A'; academic_year='2026/2027'; lecturer_id=$lecturerId}
$classUpdate = @{section='B'}
$studentCreate = @{nim='2026001'; full_name='Example Student'; email='student@example.com'}
$studentUpdate = @{email=$null}
$enrollmentCreate = @{nim='2026001'; full_name='Example Student'; email='student@example.com'}
$componentCreate = @(
  @{name='Midterm'; category='uts'; weight='40.00'; max_score='100.00'; order_index=0}
  @{name='Final'; category='uas'; weight='60.00'; max_score='100.00'; order_index=1}
)
# Isi dari GET components agar ID existing tetap dipertahankan.
$componentWrite = @(Invoke-GradeApi GET "/classes/$classId/components" | ForEach-Object {
  @{id=$_.id; name=$_.name; category=$_.category; weight=$_.weight; max_score=$_.max_score; order_index=$_.order_index}
})
$componentUpdate = @{name='Renamed assessment'}
$scorePatch = @{}
$scorePatch[$componentId] = '80.00'
# Untuk menghapus skor: $scorePatch[$componentId] = $null
```

`UserCreate` mewajibkan email, password (6–128 karakter), dan nama lengkap; role default adalah `lecturer` dan dapat diisi `superadmin`. `CourseCreate` mewajibkan kode, nama, credits berupa integer positif, dan semester. `StudentCreate` mewajibkan NIM/nama dengan email opsional. Enrollment mewajibkan NIM dan mengizinkan nama/email opsional. Untuk NIM baru, nama yang tidak dikirim memakai NIM sebagai fallback.

Nilai `null` pada update mata kuliah/kelas mempertahankan field lama. Update mahasiswa dengan `email: null` menghapus alamat. PATCH komponen menolak null eksplisit dan field yang tidak dikenal; panjang nama komponen maksimal 100 karakter, bobot positif dengan nilai maksimal 100, nilai maksimum positif, dan field desimal mengizinkan dua angka desimal. Lihat OpenAPI untuk seluruh batas panjang field dan nilai numerik.

## Kontrak response

| Kontrak | Field / komposisi |
| --- | --- |
| `UserResponse` | `id`, `email`, `full_name`, `role`, `is_active` |
| `UserRead` | Profil pengguna ditambah `created_at`, `updated_at`; tanpa hash password |
| `CourseRead` | `id`, `code`, `name`, `credits`, `semester`, `created_by`, `created_at` |
| `ClassRead` | `id`, `course_id`, `section`, `lecturer_id`, `academic_year`, `created_at`, `has_finalized_grades` |
| `StudentRead` | `id`, `nim`, `full_name`, `email` nullable, `created_at` |
| `RosterEntryRead` | Enrollment `id`, `enrolled_at`, objek `student` bersarang |
| `ComponentRead` | `id`, `class_id`, `name`, `category`, `weight`, `max_score`, `order_index`, `created_at` |
| `GradeRead` | `id`, `enrollment_id`, `final_score`, `status`, field nullable `finalized_at`, `finalized_by`, `release_notified_at` |
| `ClassGradesRead` | `class_id`, `components`, `grades`; setiap row grade memiliki `enrollment_id`, `student`, map skor, `final_score` nullable, dan `status` |
| `FinalizeRead` | `finalized_count`, `notified` (jumlah job yang diterima queue) |
| `RankingRead` | `rank`, `enrollment_id`, `student`, `final_score` |
| `HistoryRead` | `grade_id`, `enrollment_id`, objek `course` bersarang, key JSON `class`, `final_score`, field nullable `rank`/`finalized_at`, detail komponen/skor |
| `DashboardSummaryRead` | `course_count`, `class_count`, `pending_class_count`, objek `courses`/kelas bersarang, `recently_released` |
| `NotificationRead` | `id`, `grade_id`, `student_email` nullable, `status`, field nullable `error_message`/`sent_at`, `created_at` |

Status grade adalah `draft` atau `finalized`. Status notification adalah `queued`, `sent`, atau `failed`. Status kelas pada dashboard adalah `pending` atau `released`.

## Error

| HTTP | Arti |
| --- | --- |
| 401 | Token tidak ada/tidak valid, akun nonaktif, login/refresh ditolak |
| 403 | Akses role atau resource ditolak |
| 404 | Resource tidak dikenal atau enrollment di luar roster yang diminta |
| 409 | Data duplikat, record dependen, mutasi pada hasil final, rilis berulang, atau retry notification sent |
| 422 | Schema atau konfigurasi komponen tidak valid, skor di luar rentang/belum lengkap, atau credential tidak ada |
| 429 | Batas login limiter terlampaui |
| 503 | Renderer laporan yang diperlukan tidak tersedia |

Kegagalan service umumnya memakai `{ "detail": "message" }`. Kegagalan Pydantic memakai array error field di bawah `detail`. Skor finalisasi yang belum lengkap mengembalikan detail terstruktur:

```json
{
  "detail": {
    "message": "Nilai komponen belum lengkap",
    "missing": [{"student_nim": "2026001", "component_name": "Midterm"}]
  }
}
```

Setelah timeout finalisasi, baca `/classes/{class_id}/grades` sebelum retry: response yang tidak diterima tidak berarti transaksi sudah di-rollback. Rilis yang berhasil dapat terjadi bersamaan dengan kegagalan enqueue/pengiriman, yang ditangani melalui audit/retry notifikasi.

## CLI seeder

Entry point publik adalah `python -m app.seeding` dari `backend/` dengan extra `seed` terpasang. CLI ini tidak menambahkan endpoint HTTP. Lihat [seeding](seeding.md) untuk setup host/container dan credential.

| Perintah | Input | Output dan efek samping |
| --- | --- | --- |
| `plan` | Flag dataset/konfigurasi di bawah | Membangun graph tanpa akses database; menulis manifest JSON serta mencetak seed, fingerprint, jumlah row per tabel, dan path artefak |
| `apply` | Flag yang sama, `DATABASE_URL`/`APP_ENV` aman yang dipilih eksplisit, `SMTP_HOST` kosong, dan `SEED_PASSWORD` | Menambahkan dataset secara atomik atau melaporkan anchor yang sudah ada; mencetak status/jumlah row/ID hilang per tabel; menulis status manifest |
| `inspect` | Flag dataset/konfigurasi yang sama dan environment aman; tidak memerlukan password seed | Membaca ID database yang diharapkan dan melaporkan row hilang; memperbarui metadata observasi pada manifest lokal |

```powershell
python -m app.seeding plan --dataset review-v3 --profile manual --seed 20261105
python -m app.seeding apply --dataset review-v3 --profile manual --seed 20261105
python -m app.seeding inspect --dataset review-v3 --profile manual --seed 20261105
```

Contoh `apply`/`inspect` mengasumsikan database development tujuan sudah dipilih dan environment sudah dikonfigurasi sesuai [seeding](seeding.md#apply-dan-inspect-di-host).

| Flag | Kontrak |
| --- | --- |
| `--dataset` | Wajib; `[a-z0-9][a-z0-9-]{0,39}` |
| `--profile` | `manual` (default) atau `light-load` |
| `--seed` | Integer; jika tidak diisi, menghasilkan seed acak yang dicetak pada hasil |
| `--min-samples`, `--max-samples` | Override opsional, dengan `5 <= min <= max`; gunakan rentang seukuran profile untuk graph kelas berbatas |
| `--max-rows` | Batas row preflight opsional, dari 1 sampai 100.000 |
| `--reference-time` | Waktu ISO-8601 opsional dengan timezone; default `2026-01-01T00:00:00Z` |
| `--output-dir` | Root artefak relatif terhadap working directory proses; default `.artifacts/seeding` |

Profile membuat 5–15 (`manual`) atau 10–30 (`light-load`) sample per case yang dihasilkan, dengan batas default 25.000/100.000 row. Batas graph adalah 5–15 mata kuliah, 2–5 kelas per mata kuliah, dan 5–15 mahasiswa terdaftar per kelas. Kapasitas case dapat membatasi jumlah minimum mata kuliah. Fingerprint mencakup versi generator dan dependensi; gunakan parameter yang sama untuk inspect dataset, dan gunakan nama baru saat parameter berubah.

Perintah yang berhasil menghasilkan exit code 0. Kegagalan validasi/environment/fingerprint yang ditangani mencetak `error: ...` dan menghasilkan exit code 2. Kegagalan database/driver dapat memunculkan exception. Rerun tidak mereset record, password, atau edit manual. `inspect` memeriksa keberadaan record, bukan membandingkan setiap field. Konstruksi maupun apply seed tidak memublikasikan task email; row notification yang dihasilkan merupakan status simulasi.
