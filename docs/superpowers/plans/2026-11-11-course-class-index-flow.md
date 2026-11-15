# Course and Class Index Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pindahkan navigasi detail ke ikon Eye, ubah daftar kelas menjadi index table, selaraskan roster, serta pertahankan menu Courses aktif dan breadcrumb konsisten sepanjang alur course/class.

**Architecture:** Gunakan DataTable yang ada. CourseDetailPage tetap mengurus metadata, query kelas, serta dialog; CourseClassesTable menjadi komponen presentasi terfokus. Roster tetap memiliki query/dialog enrollment sendiri dan mendapatkan status lock dari ClassDetailPage. Helper navigasi menyatukan label menu berdasarkan role dan pengelompokan route; PageBreadcrumbs merender hierarki detail secara konsisten.

**Tech Stack:** React/TypeScript, TanStack Query/Table, shadcn di atas Base UI, Lucide, Vitest, React Testing Library.

**Spec:** `docs/superpowers/specs/2026-11-11-course-class-index-design.md` dan `frontend/src/features/AGENTS.md`.

## Global Constraints

- Endpoint, schema, otorisasi server, dan perhitungan nilai tidak berubah.
- Course mutation mengikuti pembuat/superadmin; class mutation mengikuti dosen pengampu/superadmin, bukan pembuat course.
- Finalisasi mengunci tambah/keluarkan roster; Eye, search, refresh, dan metadata kelas tetap mengikuti akses yang sudah ada.
- Roster row key/removal memakai enrollment ID; link detail mahasiswa memakai student ID.
- Ikuti accessible name, bobot kolom, domain pencarian, dan wireframe yang ditetapkan spec.
- Jangan menambahkan filter/statistik/route kelas baru atau lookup dosen tambahan.
- Menu Courses tetap aktif dan clickable pada route course/class, termasuk query tab. Breadcrumb root mengikuti label sidebar sesuai role dari satu helper bersama.

## Review Focus

- Dosen yang boleh membaca course tanpa boleh mengeditnya tetap bisa menggunakan Eye; uji di Task 1.
- Seksi sama pada tahun berbeda dan data course lain tidak boleh tertukar; uji scope dan label unik di Task 2.
- Lock yang berubah ketika dialog enrollment terbuka harus menutup jalur mutasi sambil menjaga Eye; uji transisi di Task 3.
- Student ID berbeda dari enrollment ID harus menghasilkan URL baca dan hapus yang berbeda dan benar; uji mutasi di Task 3 serta navigasi di Task 4.
- Search pada halaman terakhir, refresh/error, dan data panjang/null harus tetap bisa dipakai tanpa overflow; uji perilaku di Task 2/3 dan browser akhir.
- Route kelas langsung, query tab, dan metadata loading/error tidak boleh menghilangkan state aktif sidebar; label breadcrumb mengikuti role, sementara navigasi keluar tetap melewati guard draft nilai. Uji di Task 4/5.

---

### Task 1: Eye untuk detail mata kuliah

**Files:**
- Modify: `frontend/src/features/courses/CoursesPage.tsx`
- Modify: `frontend/src/features/courses/CoursesPage.test.tsx`

**Interfaces:** Course dan query `/courses` tetap; setiap baris memiliki link `Lihat mata kuliah {name}` ke `/courses/{id}`. Dialog edit/hapus tetap mengikuti permission saat ini.

- [x] **Step 1: Perbarui tes navigasi sebelum implementasi.** Ganti assertion link nama course menjadi teks nama dan link Eye berlabel `Lihat mata kuliah Pemrograman Dasar`. Pastikan `href="/courses/c1"`, navigasi bekerja dengan keyboard, dan course milik dosen lain tetap memiliki Eye meskipun edit/hapus tidak tampil. Pertahankan tes search/refresh/dialog/empty/error yang sudah ada.
- [x] **Step 2: Jalankan tes RED.** Run dari `frontend/`: `npm test -- --run src/features/courses/CoursesPage.test.tsx`. Expected: FAIL karena link Eye belum ada.
- [x] **Step 3: Ubah CoursesPage.** Jadikan nama course teks biasa; tambahkan `Eye` sebagai link ikon paling awal di kolom Tindakan, di luar kondisi owner/superadmin. Gunakan bobot 54/24/22 sesuai spec.
- [x] **Step 4: Jalankan tes GREEN.** Perintah sama; expected semua tes Courses lulus. Warna/proporsi diperiksa lewat browser, bukan assertion nama class CSS.
- [x] **Step 5: Commit.** `git add frontend/src/features/courses/CoursesPage.tsx frontend/src/features/courses/CoursesPage.test.tsx` lalu `git commit -m "feat(courses): move detail navigation to eye actions"`.

### Task 2: Daftar kelas pada course detail menjadi DataTable

**Files:**
- Create: `frontend/src/features/courses/CourseClassesTable.tsx`
- Create: `frontend/src/features/courses/CourseClassesTable.test.tsx`
- Create: `frontend/src/features/courses/CourseDetailPage.test.tsx`
- Modify: `frontend/src/features/courses/CourseDetailPage.tsx`

**Interfaces:**

```ts
interface CourseClassesTableProps {
  rows: AcademicClass[]; // Sudah terlingkup course_id oleh CourseDetailPage.
  isPending: boolean;
  isFetching: boolean;
  error: unknown;
  onRefresh: () => unknown;
  onEdit: (class_: AcademicClass) => void;
  onDelete: (class_: AcademicClass) => void;
}
export function CourseClassesTable(props: CourseClassesTableProps): React.JSX.Element;
```

Parent tetap memakai `GET /courses/{id}`, `GET /classes`, dan ClassDialog. Komponen baru tidak membuat query/endpoint sendiri.

- [x] **Step 1: Tulis tes integrasi parent dan perilaku tabel.** Pakai QueryClient serta memory router; mock API berdasarkan path. Fixture memuat kelas course aktif, kelas course lain, dan seksi A pada dua tahun berbeda. Assert hanya kelas course aktif muncul; setiap Eye berlabel section+tahun memiliki `/classes/{classId}`; edit/hapus mengirim row tepat ke dialog/callback; dosen pengampu yang bukan pembuat course tetap memiliki aksi kelas. Tambah kelas tetap membuka ClassDialog dari header.
- [x] **Step 2: Tambahkan skenario DataTable.** Search section/tahun menyaring lokal; sorting dan pagination >10 baris bekerja; mengganti search dari halaman 2 memberi hasil di halaman valid; refresh memanggil `onRefresh` dan mempertahankan search. Untuk empty/pending/error, Cari dan refresh tetap ada. Badge `Roster terkunci` hanya mengikuti `has_finalized_grades`, bukan status rilis keseluruhan.
- [x] **Step 3: Jalankan RED.** `npm test -- --run src/features/courses/CourseClassesTable.test.tsx src/features/courses/CourseDetailPage.test.tsx`. Expected: komponen belum tersedia atau parent belum menampilkan tabel.
- [x] **Step 4: Implementasikan CourseClassesTable dan integrasikan parent.** Kolom Kelas/Tahun akademik/Status roster/Tindakan memakai bobot 28/26/26/20. Search Cari inline dan refresh berada pada card DataTable, dengan page size/pagination bawaan. Eye netral; edit biru; hapus destructive. Parent tetap memfilter `course_id` dan memiliki seluruh state dialog. Hapus grid card, link judul kelas, tombol Buka kelas, dan NoData terpisah yang digantikan state tabel. Error query kelas ditampilkan dengan QueryState tanpa menghilangkan toolbar; metadata course yang gagal tetap memakai penanganan parent saat ini.
- [x] **Step 5: Jalankan GREEN.** Perintah Step 3 ditambah `src/features/courses/CoursesPage.test.tsx`; expected semua tes terkait lulus. Pastikan source komponen baru bertipe dan tidak membuat lookup dosen/jumlah mahasiswa.
- [x] **Step 6: Commit.** Stage empat file task ini; `git commit -m "feat(classes): render course classes as an index table"`.

### Task 3: Selaraskan roster mahasiswa kelas

**Files:**
- Modify: `frontend/src/features/classes/Roster.tsx`
- Modify: `frontend/src/features/classes/Roster.test.tsx`

**Interfaces:** `Roster({ classId, locked }: { classId: string; locked: boolean })` tetap. Pertahankan EnrollmentDialog dan RemoveEnrollmentDialog; query `/classes/{classId}/roster` serta adapter mutasi yang ada tetap dipakai.

- [x] **Step 1: Perluas tes roster sebelum mengubahnya.** Harness memakai QueryClient dan API palsu agar dialog/request bisa diperiksa. Assert Cari menyaring nama/NIM/email tanpa request baru; refresh hanya mengulang roster kelas aktif; data kosong/pending/error tetap memiliki card dan kontrol. Verifikasi sorting, pagination >10 row, email null/panjang, serta hasil search kosong.
- [x] **Step 2: Tulis tes navigasi dan lock.** Link `Lihat mahasiswa Budi (001)` harus ke `/students/student-1` ketika `RosterEntry.id="enrollment-1"`. Dalam kondisi locked, Eye tetap ada, tambah disabled, dan Keluarkan hilang. Rerender unlocked→locked saat dialog tambah/keluar terbuka harus membuat dialog tersebut tidak lagi dapat disubmit. Tidak ada edit/hapus profil global mahasiswa dari roster.
- [x] **Step 3: Tulis tes mutasi enrollment yang dipertahankan.** Menambahkan NIM terdaftar mengirim NIM saja; mahasiswa baru mengirim NIM/nama/email yang diisi. Konfirmasi keluar mengirim `DELETE /classes/class-1/enrollments/enrollment-1`, bukan student ID atau endpoint `/students`. Respons 409 tetap ditampilkan dan memicu invalidasi query melalui adapter yang ada.
- [x] **Step 4: Jalankan RED.** `npm test -- --run src/features/classes/Roster.test.tsx`. Expected: FAIL pada Cari, Eye, atau toolbar yang saat ini belum ada; tes mutasi lama/kontrak yang sudah bekerja boleh lulus sebagai baseline.
- [x] **Step 5: Implementasikan revisi Roster.** Nama/NIM menjadi teks biasa; kolom Tindakan selalu ada untuk Eye dan hanya menambahkan Trash keluar bila unlocked. Gunakan bobot 40/38/22 dan wrapping nama/email sesuai aturan. Tambah search state lokal; pindahkan refresh dari header ke `DataTable.actions`; pertahankan tombol tambah di header bagian roster. Render DataTable pada semua state dengan pesan loading/empty/search-empty yang jelas; error query tetap melalui QueryState. Pertahankan guard `adding && !locked` serta `removing && !locked`.
- [x] **Step 6: Jalankan GREEN.** Perintah sama; expected seluruh tes roster lulus termasuk lock, dialog, endpoint, dan invalidasi. Jika prop classId berubah, query/tautan/aksi harus memakai kelas yang baru.
- [x] **Step 7: Commit.** Stage dua file task ini; `git commit -m "feat(classes): align roster table and detail actions"`.

### Task 4: Sidebar aktif dan breadcrumb sesuai menu

**Files:**
- Create: `frontend/src/lib/navigation.ts`
- Create: `frontend/src/lib/navigation.test.ts`
- Create: `frontend/src/components/PageBreadcrumbs.tsx`
- Create: `frontend/src/components/PageBreadcrumbs.test.tsx`
- Modify: `frontend/src/components/Sidebar.tsx`
- Modify: `frontend/src/components/Layout.test.tsx`
- Modify: `frontend/src/features/courses/CourseDetailPage.tsx`
- Modify: `frontend/src/features/classes/ClassDetailPage.tsx`

**Interfaces:**

```ts
export function getCourseMenuLabel(role: string): string;
export function isSidebarItemActive(target: string, pathname: string): boolean;

export interface BreadcrumbItem { label: string; to?: string }
export function PageBreadcrumbs(props: {
  items: readonly BreadcrumbItem[];
}): React.JSX.Element;
```

`getCourseMenuLabel` menghasilkan `Semua Mata Kuliah` untuk superadmin dan `Mata Kuliah Saya` untuk lecturer. `isSidebarItemActive` menangani alias route kelas untuk target `/courses`; perilaku menu lain mengikuti batas segmen yang ada (Dashboard exact). PageBreadcrumbs merender ancestor sebagai Link dan item terakhir sebagai teks current page.

- [x] **Step 1: Tulis tes navigasi RED.** Di `navigation.test.ts`, uji `/courses`, `/courses/c1`, `/classes/k1` aktif untuk target `/courses`, tetapi `/courses-archive`, `/classes-other`, dan `/students/s1` tidak. Di `Layout.test.tsx`, sediakan route list/detail course/class dan role superadmin/lecturer. Assert menu berlabel sesuai role memiliki `aria-current="page"`, href `/courses`, serta tetap bisa diklik dari detail class. Uji query `?tab=grades` dan `?tab=analytics`, hanya satu menu aktif, serta perpindahan ke detail mahasiswa memindahkan state aktif ke Mahasiswa.
- [x] **Step 2: Tulis tes breadcrumb.** Assert urutan root→course→class sesuai spec, ancestor memiliki href yang benar, separator tidak masuk accessible name, dan item terakhir saja current page di dalam nav Breadcrumb. Label root untuk kedua role harus identik dengan menu, bukan hardcoded `Mata kuliah`. Data panjang dimasukkan untuk pemeriksaan browser tanpa assertion nama class CSS.
- [x] **Step 3: Jalankan RED.** Dari `frontend/`: `npm test -- --run src/lib/navigation.test.ts src/components/PageBreadcrumbs.test.tsx src/components/Layout.test.tsx`. Expected: helper/component belum tersedia atau menu tidak aktif pada route kelas.
- [x] **Step 4: Implementasikan helper, sidebar, dan breadcrumb.** Sidebar menggunakan helper untuk label dan active state berdasarkan `useLocation().pathname`. Pakai Link semantik dengan active class dan aria-current yang dihitung bersama agar alias `/classes/:id` juga benar secara aksesibilitas; Dashboard tetap exact dan menu lain tetap segment-aware. Jangan menambahkan disabled pada menu aktif atau memaksa sidebar mobile terbuka. Ganti breadcrumb inline CourseDetailPage/ClassDetailPage dengan PageBreadcrumbs; course ancestor menampilkan nama, current kelas memakai section+tahun. Gunakan data query yang sudah ada, tanpa request metadata tambahan.
- [x] **Step 5: Jalankan GREEN dan regresi detail.** Perintah Step 3 ditambah `src/features/courses/CourseDetailPage.test.tsx`, `src/features/grades/GradeEntryGrid.test.tsx`, dan `src/features/analytics/AnalyticsPages.test.tsx`; expected PASS. Klik menu/breadcrumb dari kelas tetap memakai router Link, sehingga GradeNavigationGuard masih bekerja.
- [x] **Step 6: Commit.** Stage hanya file task ini; `git commit -m "fix(navigation): preserve course context and breadcrumbs"`.

### Task 5: Verifikasi alur course → class → mahasiswa

**Files:**
- Create: `frontend/src/features/courses/CourseClassFlow.test.tsx`

**Interfaces:** Gunakan Layout, CoursesPage, CourseDetailPage, dan ClassDetailPage aktual pada memory router. Tujuan `/students/:studentId` boleh berupa stub read-only yang menampilkan parameter ID; halaman analytics mahasiswa sendiri berada di luar perubahan ini.

- [x] **Step 1: Tambahkan tes rute gabungan.** Fixture API memuat satu course, dua kelas berbeda course, dan roster dengan student/enrollment ID berbeda. Buka `/courses`, ikuti Eye course → Eye kelas → Eye mahasiswa; assert setiap route dan ID benar. Ulangi kelas locked untuk memastikan akses baca tetap bekerja, tambah/keluar terblokir. Route kelas langsung juga harus memuat konteks course dan roster yang benar. Sepanjang route course/class, assert menu Courses tetap aktif dan ancestor breadcrumb mengikuti label role; navigasi Eye ke mahasiswa mengaktifkan menu Mahasiswa. Uji menu tetap aktif ketika metadata/query kelas loading atau gagal, tanpa menampilkan ID mentah sebagai breadcrumb nama.
- [x] **Step 2: Jalankan tes alur dan regresi detail kelas.** `npm test -- --run src/features/courses/CourseClassFlow.test.tsx src/features/grades/GradeEntryGrid.test.tsx src/features/analytics/AnalyticsPages.test.tsx`. Expected: PASS; perpindahan tab dan guard draft nilai tetap berfungsi. Tes alur ini adalah verifikasi integrasi atas task yang sudah selesai, tidak mensyaratkan kegagalan buatan.
- [x] **Step 3: Jalankan pemeriksaan frontend akhir.** Dari `frontend/`: `npm test`, `npm run build`, `npm run lint`. Expected: semua tes lulus, build/lint exit 0; laporkan warning lama secara akurat.
- [x] **Step 4: Periksa browser pada lebar 1280 dan 390 px.** Gunakan data fixture atau akun test yang sesuai untuk role pembuat course, dosen pengampu non-pembuat, dan superadmin. Periksa Eye/link keyboard, tiga ikon tidak meluber, tabel kelas terlingkup course, wrapping email, toolbar inline, error/empty/loading, serta roster locked. Periksa menu Courses tetap terpilih dan bisa diklik selama tab class berubah; breadcrumb nama panjang wrap dan root sesuai menu role. Sidebar mobile tetap dapat dibuka/ditutup pengguna. Jika memakai server fixture, dokumentasikan bahwa verifikasi bukan mutasi data manual pengguna.
- [x] **Step 5: Commit tes alur.** `git add frontend/src/features/courses/CourseClassFlow.test.tsx` lalu `git commit -m "test: cover course class roster navigation"`.

### Penyelesaian

- [x] Tandai progres plan dan catat hasil verifikasi serta keputusan eksekusi.
- [x] Lakukan satu review akhir seluruh diff terhadap spec dan AGENTS.md; perbaiki temuan penting dengan tes reproduksi yang relevan.
- [ ] Integrasi ke branch lokal dan restart container dilakukan setelah pengguna memilih langkah integrasi; simpan pekerjaan di worktree sampai saat itu.

### Hasil eksekusi (15 November 2026)

- Task 1-5 selesai pada branch `course-class-index-flow`, dari base `02357c4` sampai `bddd84a`. Implementasi dipisah menjadi commit Eye course, tabel kelas, roster, navigasi, dan tes alur.
- Frontend: 128 tes dalam 19 file lulus; build dan lint exit 0 setelah sesi dilanjutkan. Lint masih melaporkan dua warning sebelumnya: `react(incompatible-library)` pada DataTable dan `react(only-export-components)` pada primitive Button.
- Pemeriksaan browser menggunakan frontend worktree di port 15174 dan API fixture sementara di port 18001, tanpa mengubah data aplikasi pengguna. Diperiksa pada 1280 dan 390 px untuk dosen pembuat, dosen pengampu non-pembuat, dan superadmin: scope course, Eye/Enter, toolbar, tiga ikon tindakan, wrapping email/breadcrumb panjang, roster terkunci, serta empty/error/loading. Tidak ada overflow halaman atau sel; tabel mobile dapat digeser horizontal.
- Semua tab kelas mempertahankan menu Courses aktif dan clickable. Breadcrumb root mengikuti role. Buka/tutup sidebar mobile diverifikasi, termasuk perubahan `aria-expanded` dari true menjadi false melalui tombol tutup.
- Satu reviewer independen memeriksa keseluruhan diff, kontrak backend, aturan index, dan keputusan eksekusi: tidak ada temuan Critical/Important. Reviewer menjalankan `git diff --check`; tes/browser dilaksanakan oleh implementer.

**Keputusan eksekusi dan konsekuensi:**

1. Plan/spec yang sebelumnya untracked dimasukkan ke commit persiapan agar input eksekusi tersedia dalam history. Konsekuensi: satu commit dokumentasi tambahan.
2. Commit memakai `commit.gpgsign=false` per perintah karena secret key GPG tidak tersedia. Konsekuensi: commit tidak ditandatangani; konfigurasi Git tidak diubah.
3. Assertion label breadcrumb pada tes analytics disesuaikan menjadi `Mata Kuliah Saya`, sesuai perubahan yang diminta. Konsekuensi: satu file tes lama ikut berubah; assertion guard draft tetap dipertahankan.
4. Reuse Roster mandiri dengan `classId` baru saat dialog pengeluaran terbuka tidak diperluas: halaman produksi meremount konten kelas dan roster berdasarkan ID. Konsekuensi jika dipakai tanpa remount di masa depan: state dialog lama perlu direset oleh pemanggil atau roster.
5. Retensi state dialog pada transisi unlocked-locked-unlocked mengikuti perilaku sebelumnya; selama locked, dialog tidak dirender dan mutasi diblokir. Konsekuensi: dialog dapat muncul kembali setelah kelas dibuka kuncinya.
6. Pemeriksaan penutupan sidebar mobile yang tidak dilakukan reviewer sudah diselesaikan implementer melalui browser fixture. Batas bukti: pemeriksaan tersebut tidak memakai akun/data aplikasi nyata.

**Minor ditunda:** Ketiga Eye memakai Base UI Button yang dirender sebagai Link dengan default `nativeButton=true`, sehingga muncul peringatan console. Role link dan navigasi Enter tetap bekerja. Tindak lanjut terpisah: gunakan `nativeButton={false}` sambil mempertahankan `role="link"`, atau style Link memakai `buttonVariants`; verifikasi role, Enter, dan hilangnya peringatan.

Integrasi ke `master` dan restart container belum dijalankan; langkah ini menunggu pilihan integrasi pengguna sesuai plan.
