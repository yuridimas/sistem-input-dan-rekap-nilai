# Course, Class, dan Roster Index Design

## Tujuan dan cakupan

Standarkan alur `/courses` → `/courses/:courseId` → `/classes/:classId` → detail mahasiswa dengan aturan `frontend/src/features/AGENTS.md`. Detail pada baris daftar dibuka melalui ikon `Eye` di kolom Tindakan. Daftar kelas dalam detail mata kuliah menjadi DataTable; roster mahasiswa kelas mengikuti pola index yang sama. Menu Courses tetap aktif dan dapat diklik sepanjang alur course/class, dengan breadcrumb yang mengikuti nama menu pengguna.

## Evaluasi kondisi saat ini

| Area | Implementasi sekarang | Perubahan yang diperlukan |
| --- | --- | --- |
| CoursesPage | DataTable sudah standar; nama mata kuliah menjadi link detail; kolom Tindakan hanya edit/hapus | Pindahkan akses detail ke link ikon Eye yang tersedia untuk setiap baris yang boleh dibaca |
| CourseDetailPage | Query metadata course dan `/classes`, lalu memfilter `course_id`; kelas berupa grid card dengan link judul dan tombol Buka kelas | Ganti card dengan tabel kelas terlingkup course, search lokal, refresh, sorting, dan pagination |
| Roster | Sudah DataTable untuk data berisi; nama mahasiswa menjadi link; refresh di header; belum ada search; empty/error/loading mengganti tabel | Tambahkan search, pindahkan refresh ke toolbar tabel, pertahankan card/controls pada semua state, dan pindahkan link detail ke Eye |
| Roster terkunci | Tambah disabled, aksi keluar disembunyikan, dialog mutasi tidak dirender | Pertahankan pembatasan tersebut; Eye/search/refresh tetap tersedia |
| Sidebar | NavLink `/courses` aktif pada turunannya, tetapi `/classes/:id` berada pada path lain | Kelompokkan `/courses` dan detail `/classes/:id` sebagai satu menu Courses, termasuk seluruh query tab |
| Breadcrumb | Root ditulis `Mata kuliah`, sementara menu berlabel sesuai role; course ditampilkan sebagai kode | Gunakan label root menu yang sama, nama mata kuliah sebagai konteks, dan kelas sebagai halaman aktif |

## Kontrak dan batas akses

- `GET /courses` dan `GET /courses/{id}` tetap menjadi sumber data mata kuliah. Edit/hapus course hanya untuk pembuat atau superadmin.
- `GET /classes` sudah membatasi hasil sesuai pengguna; frontend tetap memfilter `course_id` sebelum menampilkan kelas di course detail. Endpoint ini tidak mendukung filter course/search/pagination server.
- `AcademicClass` memiliki `id`, `course_id`, `section`, `academic_year`, `lecturer_id`, dan `has_finalized_grades`. Nama dosen, jumlah mahasiswa, dan waktu update tidak tersedia pada kontrak frontend; kolom-kolom tersebut tidak ditambahkan.
- Kelas dibaca/dikelola dosen pengampu atau superadmin. Hak edit course tidak boleh digunakan sebagai syarat aksi baris kelas.
- `has_finalized_grades` berarti sedikitnya satu nilai sudah finalized; ini bukan penanda seluruh kelas sudah dirilis. Label tabel adalah **Roster terkunci** atau **Roster terbuka**.
- Lock finalisasi menahan tambah/keluarkan enrollment; edit metadata kelas tetap mengikuti perilaku server saat ini. Hapus kelas bisa ditolak 409 karena relasi yang masih ada.
- Roster memakai `GET /classes/{classId}/roster`. `RosterEntry.id` adalah enrollment ID; `RosterEntry.student.id` adalah student ID. Detail memakai student ID, keluar kelas memakai enrollment ID.
- Pengeluaran mahasiswa hanya menghapus enrollment. Tidak ada aksi edit/hapus profil global mahasiswa yang ditambahkan ke roster.
- Dialog create/edit/delete/enrollment dan invalidasi query akademik/dashboard tetap menggunakan pola yang sudah ada. Respons 403/404/409 tetap diproses oleh adapter mutasi saat ini.

## Keputusan tampilan

1. Navigasi detail dalam ketiga daftar dipusatkan pada kolom Tindakan; nama objek menjadi teks biasa. Navigasi ancestor di breadcrumb tetap berupa link.
2. Ikon Eye memakai link semantik melalui `Button render={<Link ... />}`, `size="icon"`, `variant="outline"`, dan `aria-label` spesifik. Link tetap dapat dibuka di tab baru.
3. Accessible name: `Lihat mata kuliah {name}`, `Lihat kelas {section} ({academic_year})`, dan `Lihat mahasiswa {full_name} ({nim})`. Gunakan section beserta tahun juga pada label edit/hapus kelas untuk membedakan seksi yang sama lintas tahun.
4. Kelas tetap berada di course detail, bukan route index `/classes` baru. `CourseDetailPage` memiliki query/dialog; komponen presentasi `CourseClassesTable` memiliki search lokal dan definisi kolom.
5. Kolom course: Mata kuliah 54, Semester/SKS 24, Tindakan 22. Kolom kelas: Kelas 28, Tahun akademik 26, Status roster 26, Tindakan 20. Kolom roster: Mahasiswa 40, Email 38, Tindakan 22. Angka adalah bobot `ColumnDef.size` yang dinormalisasi DataTable.
6. Tabel kelas mencari section/tahun akademik; roster mencari nama/NIM/email. Label **Cari** inline dengan input dan refresh tetap sejajar ketika ruang cukup, termasuk viewport 390 px.
7. Page size, sorting, dan pagination memakai DataTable yang ada. Refresh kelas memanggil query `/classes`; refresh roster memanggil query roster kelas aktif. Toolbar/card tetap ada saat data kosong, loading, dan error; error tampil melalui QueryState.
8. Tombol Tambah kelas tetap di header course detail. Tombol Tambah mahasiswa ke kelas tetap di header bagian roster dan disabled saat locked. Tombol keluar destructive; edit biru; Eye netral.
9. Menu Courses terpilih pada `/courses`, `/courses/:courseId`, dan `/classes/:classId`, termasuk `?tab=students|components|grades|analytics`. Gunakan pathname dengan batas segmen agar `/courses-archive` atau `/classes-other` tidak ikut aktif. Menu aktif memakai styling terpilih dan `aria-current="page"`, tetap link ke `/courses`, serta tidak memiliki disabled/pointer-events yang menghalangi klik. Setelah masuk `/students/:studentId`, menu Mahasiswa menjadi aktif. Perilaku buka/tutup sidebar mobile tetap mengikuti kontrol pengguna.
10. Label root menu/breadcrumb berasal dari helper yang sama: superadmin **Semua Mata Kuliah**, lecturer **Mata Kuliah Saya**. Course detail: `{label menu}` → `{course.name}`. Class detail: `{label menu}` → `{course.name}` → `Kelas {section} ({academic_year})`. Root dan course ancestor menuju route yang benar; item terakhir teks dengan `aria-current="page"`. Gunakan `nav aria-label="Breadcrumb"`, list semantik, separator dekoratif, serta wrapping label panjang. Tab tidak menambah level breadcrumb dan tidak menghilangkan pilihan menu Courses.

## Contoh breadcrumb

| Halaman | Superadmin | Dosen |
| --- | --- | --- |
| Course detail | Semua Mata Kuliah → Pemrograman Dasar | Mata Kuliah Saya → Pemrograman Dasar |
| Class detail | Semua Mata Kuliah → Pemrograman Dasar → Kelas A (2026/2027) | Mata Kuliah Saya → Pemrograman Dasar → Kelas A (2026/2027) |

Courses index tetap memakai judul halaman yang sesuai role; tidak perlu menambahkan breadcrumb satu level yang menduplikasi judulnya.

## Wireframe yang masuk scope

### `/courses/:courseId`

```text
[Sidebar: menu Courses aktif dan tetap link]
[Breadcrumb: {Semua Mata Kuliah | Mata Kuliah Saya} / {Nama mata kuliah}]
[Judul course + deskripsi]                    [Edit mata kuliah] [+ Tambah kelas]

Daftar kelas
+----------------------------------------------------------------------------+
| Baris per halaman [10]                     Cari [Seksi atau tahun] [Refresh] |
|----------------------------------------------------------------------------|
| Kelas       | Tahun akademik | Status roster    | Tindakan                  |
| Kelas A     | 2026/2027      | Roster terbuka   | [Eye] [Pencil] [Trash]     |
|----------------------------------------------------------------------------|
| 1–10 dari N baris                          Halaman X/Y [Sebelumnya][Berikut] |
+----------------------------------------------------------------------------+
```

Edit mata kuliah hanya muncul bagi pembuat/superadmin. Kelas yang tampil sudah terlingkup course dan pengguna. Tidak ada kartu statistik atau filter tambahan.

### Tab Mahasiswa `/classes/:classId`

```text
[Sidebar: menu Courses aktif dan tetap link]
[Breadcrumb: {Nama menu Courses} / {Nama mata kuliah} / Kelas A (2026/2027)]
[Konteks kelas dan tab yang sudah ada]
[Peringatan lock bila kelas memiliki nilai finalized]

Daftar mahasiswa kelas                      [+ Tambah mahasiswa ke kelas]
+----------------------------------------------------------------------------+
| Baris per halaman [10]                  Cari [Nama, NIM, email] [Refresh]   |
|----------------------------------------------------------------------------|
| Mahasiswa + NIM        | Email (wrap)               | Tindakan              |
| Dewi / 2026001         | dewi@academic.example.test | [Eye] [Trash keluar]  |
|----------------------------------------------------------------------------|
| 1–10 dari N baris                          Halaman X/Y [Sebelumnya][Berikut] |
+----------------------------------------------------------------------------+
```

Saat locked, tombol tambah disabled dan Trash keluar tidak tampil; kolom Tindakan tetap ada untuk Eye.

## Kriteria penerimaan

- Eye navigasi tampil pada baris course, kelas, dan roster yang boleh dibaca, termasuk course non-owner dan roster locked.
- Nama baris tidak lagi menjadi link detail kedua; breadcrumb tetap link.
- Menu Courses memiliki indikator aktif/aria-current dan tetap dapat diklik pada index course, detail course, detail class, serta seluruh tab class; pilihan menu tidak bergantung pada keberhasilan query metadata.
- Breadcrumb root identik dengan label menu untuk role yang aktif; ancestor menavigasi dengan benar dan hanya item terakhir menjadi current page. Label panjang tetap dapat dibaca pada mobile.
- Detail course hanya menampilkan kelas milik course itu dari hasil query yang sudah terotorisasi.
- Tabel kelas dan roster memiliki page size, Cari inline, refresh, sorting, pagination, serta state kosong/loading/error yang konsisten.
- Search tidak membuat request API; refresh tidak mereset search.
- Mutasi/dialog dan error 409 tetap benar; kelas locked tidak dapat ditambah/dikeluarkan mahasiswa melalui UI.
- Email null/panjang, nama panjang, dan tombol aksi tidak meluber ke kolom sebelah; tabel boleh scroll horizontal pada layar kecil tanpa membuat halaman ikut overflow.
- Tab nilai/komponen/analisis, download laporan, dan guard draft nilai tidak berubah.

## Di luar pekerjaan ini

Perubahan endpoint/schema, statistik baru, filter baru, edit/hapus profil mahasiswa dari roster, perubahan perhitungan nilai, serta penggantian layout dashboard atau halaman detail mahasiswa.
