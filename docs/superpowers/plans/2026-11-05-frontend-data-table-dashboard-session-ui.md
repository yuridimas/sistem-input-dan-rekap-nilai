# Refactor Data Table, Dashboard, dan Profil Sesi Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Standarkan tabel operasional dengan pola Data Table bergaya shadcn di atas Base UI, lalu pecah dashboard dan informasi pengguna login menjadi komponen yang mudah dipelihara.

**Architecture:** Pertahankan primitive tabel semantik yang ada dan tambahkan abstraksi Data Table berbasis TanStack Table untuk kolom, sorting, pencarian, filter yang memang dipakai halaman, dan pagination di sisi klien. Migrasikan halaman daftar operasional secara bertahap; tabel analitik dan grid nilai yang berfungsi sebagai laporan/input matriks tetap memakai primitive semantik. Dashboard menampilkan lima mata kuliah terbaru berdasarkan `created_at`; kontrak ringkasan perlu menyertakan timestamp tersebut. Profil sesi dan tombol keluar berada di sidebar bawah, sementara sisi kanan header menampilkan akses notifikasi.

**Tech Stack:** React 19, TypeScript, Base UI, shadcn-style local components, Tailwind CSS 4, TanStack Table, React Query, Zustand, Vitest, React Testing Library.

**Spec:** Belum ada spec khusus; keputusan cakupan dan wireframe pada dokumen ini menjadi acuan implementasi.

## Global Constraints

- Pertahankan React 19, TypeScript, Base UI, Tailwind CSS 4, dan konvensi import `@/`.
- Data Table hanya mengelola presentasi data yang sudah tersedia di halaman; perubahan kontrak dashboard dibatasi pada timestamp mata kuliah untuk menentukan lima mata kuliah terbaru.
- Pertahankan semantik tabel, state loading/error/kosong, akses keyboard, label aksesibel, dan kontrol role yang sekarang.
- Jangan migrasikan grid input nilai atau tabel ringkasan analitik ke Data Table jika sorting/filter/pagination tidak sesuai dengan fungsi matriks/laporan.
- Pertahankan API `Table`, `TableHeader`, `TableBody`, `TableRow`, `TableHead`, dan `TableCell` untuk tabel statis yang tidak dimigrasikan.
- Gunakan versi TanStack Table yang kompatibel dengan toolchain TypeScript proyek; dokumentasikan dependency baru dalam lockfile.
- UI menggunakan teks Bahasa Indonesia seperti pola halaman saat ini.

## Review Focus

- Sorting tetap deterministik untuk nilai teks, angka, tanggal, dan kolom opsional; pin dengan test konfigurasi/render tabel yang relevan.
- Pencarian dan filter tidak mengubah data sumber atau kontrak request; pin dengan test halaman yang dimigrasikan.
- Pagination menangani dataset kosong, satu halaman, dan perpindahan halaman terakhir setelah filter berubah; pin dengan test DataTable.
- Tabel tetap dapat dipakai pada viewport sempit dan pembaca layar; pin dengan test nama aksesibel/label kontrol serta review DOM dan wireframe responsif.
- Tabel tetap menghormati role dan aksi yang tersedia; pin dengan test halaman admin/lecturer yang memiliki kolom tindakan kondisional.

---

## Wireframe

### Daftar operasional desktop

```text
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Judul halaman                                         [Aksi utama]      â”‚
â”‚ Deskripsi singkat                                                        â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ [Cari ...                                                  ]             â”‚
â”‚ 24 baris                                                                  â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚   â”‚ Kolom data              â”‚ Kolom data       â†• â”‚ Kolom data               â”‚
â”‚   â”‚ Isi baris                â”‚ Isi baris           â”‚ Isi baris                 â”‚
â”‚   â”‚ ...                      â”‚ ...                 â”‚ ...                       â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ 24 baris                                        [â€¹] 1  2  3 [â€º]         â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

Wireframe ini hanya memuat pencarian, kolom data, dan pagination. Filter spesifik halaman serta aksi yang sudah ada tetap direncanakan pada task halaman terkait, tanpa mengasumsikan semuanya muncul pada setiap tabel. Sorting tersedia hanya untuk kolom yang dinyatakan sortable.

### Daftar operasional layar sempit

```text
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Judul             [Aksi]     â”‚
â”‚ Deskripsi                    â”‚
â”‚ [Cari....................]  â”‚
â”‚ [Filter â–¾] [Reset]           â”‚
â”‚ â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”‚
â”‚ â”‚ Identitas utama          â”‚ â”‚
â”‚ â”‚ Email / data pendukung   â”‚ â”‚
â”‚ â”‚ Status            [â‹¯]    â”‚ â”‚
â”‚ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â”‚
â”‚ 1â€“10 dari 24      [â€¹] [â€º]    â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

Untuk kolom tabel yang tidak muat, container tabel tetap dapat digulir horizontal dengan header yang jelas. Perubahan ke kartu per baris hanya dilakukan untuk halaman yang desain saat ini memang menyembunyikan/mengatur ulang kolom pada mobile, bukan sebagai transformasi otomatis library.

### Dashboard

```text
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Dashboard                                                          â”‚
â”‚ Ringkasan sesuai peran pengguna                                     â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ [Mata kuliah]        [Jumlah kelas]         [Belum dirilis]         â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ Mata Kuliah Saya / Semua Mata Kuliah   â”‚ Rilis Terbaru             â”‚
â”‚ Maksimal 5 terbaru       [Lihat semua] â”‚ Daftar rilis ringkas      â”‚
â”‚ [CourseOverview]                       â”‚                           â”‚
â”‚ ... hingga 5                            â”‚                           â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

Ekstraksi dashboard mempertahankan hierarki dan perilaku yang sudah ada: kartu statistik, ekspansi `CourseOverview`, state loading/error, dan fokus ke kelas dari item rilis. Daftar kursus dibatasi lima item terbaru berdasarkan waktu pembuatan; tautan â€œLihat semuaâ€ menuju halaman mata kuliah, sedangkan angka total tetap mencerminkan seluruh data.

### Profil pengguna sesi

```text
Header desktop: [Judul halaman]                                  [Notifikasi]
Sidebar bawah:  [Inisial] Nama / Email / Peran
                [Keluar]

Header mobile:  [â˜°] [Judul halaman]                         [Notifikasi]
Sidebar mobile setelah dibuka: identitas, peran, dan tombol keluar di bawah
Sidebar menu: Dashboard / Mata Kuliah / Mahasiswa / Pengguna (admin)
```

Profil sesi dan tombol keluar hanya muncul di bagian bawah sidebar untuk menghindari duplikasi. Item notifikasi dihapus dari sidebar dan dipindahkan ke kontrol di sisi kanan header. Layout tetap menjadi pemilik logout dan state autentikasi.

## File Map

- Create `frontend/src/components/data-table/DataTable.tsx`: adapter generik TanStack Table ke primitive Base UI/shadcn lokal.
- Create `frontend/src/components/data-table/DataTablePagination.tsx`: kontrol jumlah baris dan navigasi halaman yang aksesibel.
- Create `frontend/src/components/data-table/DataTableToolbar.tsx`: slot pencarian, filter, dan aksi halaman tanpa mengunci domain.
- Create `frontend/src/components/data-table/index.ts`: ekspor tipe dan komponen publik internal.
- Modify `frontend/src/components/ui/table.tsx`: penyesuaian visual/aksesibilitas dasar bila perlu, tanpa memutus API primitive.
- Modify `frontend/package.json` dan lockfile: dependency runtime TanStack Table.
- Migrate list pages: `features/users/UsersPage.tsx`, `features/courses/CoursesPage.tsx`, `features/students/StudentsPage.tsx`, `features/notifications/NotificationsPage.tsx`, dan `features/classes/Roster.tsx`, setelah memverifikasi fitur sorting/filter/action masing-masing.
- Keep semantic table consumers: `features/grades/GradeEntryGrid.tsx`, `features/analytics/ClassCharts.tsx`, `features/analytics/StudentTrend.tsx`, `features/reports/StudentReportList.tsx`, dan tabel lain yang berfungsi sebagai matriks/laporan statis.
- Create `frontend/src/features/dashboard/SummaryCards.tsx` dan `frontend/src/features/dashboard/RecentReleases.tsx`; modify `DashboardPage.tsx` untuk komposisi.
- Modify dashboard schema/service/repository backend serta `features/dashboard/api.ts` untuk menyertakan `created_at` mata kuliah pada ringkasan.
- Create `frontend/src/components/SessionProfile.tsx`; modify `Layout.tsx` dan `Sidebar.tsx` untuk memakai profil bersama dengan placement yang sesuai.
- Tambahkan/ubah test unit di direktori fitur terkait serta test komponen generik di `frontend/src/components/data-table/`.

## Global Interfaces

- `DataTable<TData, TValue>` menerima `columns: ColumnDef<TData, TValue>[]`, `data: TData[]`, `getRowId?`, `emptyMessage?`, dan konfigurasi pagination awal opsional; tabel tidak mengambil data sendiri.
- `DataTableToolbar` menerima child controls melalui `children` dan slot aksi opsional; filter spesifik domain tetap dimiliki halaman fitur.
- `DataTablePagination` menerima instance tabel TanStack, label jumlah baris, dan opsi page size yang ditentukan halaman.
- `SessionProfile` menerima `user: AuthUser` dan `onLogout`; tampilkan nama, email, peran, inisial, serta tombol keluar hanya di bagian bawah Sidebar.
- Kontrol notifikasi di header berupa tautan ke `/notifications`, ditampilkan hanya bagi superadmin sesuai akses route yang ada.
- Kartu dashboard dan rilis menerima tipe response yang sudah diekspor/didefinisikan pada `features/dashboard/api.ts`; keduanya tidak memanggil API secara mandiri.

## Task 1: Tambahkan fondasi Data Table

**Files:**
- Create: `frontend/src/components/data-table/DataTable.tsx`
- Create: `frontend/src/components/data-table/DataTablePagination.tsx`
- Create: `frontend/src/components/data-table/DataTableToolbar.tsx`
- Create: `frontend/src/components/data-table/index.ts`
- Modify: `frontend/package.json`, lockfile
- Test: `frontend/src/components/data-table/DataTable.test.tsx`

**Interfaces:** Ikuti `Global Interfaces`. Gunakan row model core, filtered, sorted, dan pagination dari TanStack Table; jangan menambahkan fetch atau state global.

- [x] Tambahkan `@tanstack/react-table` sebagai dependency dan pastikan lockfile konsisten.
- [x] Tulis test untuk render kolom/baris, sorting, pencarian via toolbar caller, halaman kosong, dan perpindahan pagination.
- [x] Implementasikan adapter DataTable menggunakan `flexRender` dan primitive lokal dari `components/ui/table`.
- [x] Implementasikan kontrol pagination dengan label aksesibel, disabled state di batas halaman, dan page size.
- [x] Implementasikan toolbar berbasis slot sehingga kontrol domain tetap di halaman pemanggil.
- [x] Verifikasi hasil TypeScript, test komponen, dan lint frontend.

## Task 2: Migrasikan daftar pengguna, mata kuliah, dan mahasiswa

**Files:**
- Modify: `frontend/src/features/users/UsersPage.tsx`
- Modify: `frontend/src/features/courses/CoursesPage.tsx`
- Modify: `frontend/src/features/students/StudentsPage.tsx`
- Modify corresponding existing page tests.

**Interfaces:** Halaman tetap memiliki query React Query, pencarian/filter domain, dialog, dan aturan role. DataTable menerima hasil terfilter dan definisi kolom halaman.

- [x] Ubah setiap halaman untuk menyediakan `ColumnDef` dengan ID stabil; render link, badge, dan tombol aksi melalui `cell`.
- [x] Pertahankan loading/error/empty state di lapisan halaman dan gunakan `DataTable` hanya saat ada baris.
- [x] Pastikan pencarian/filter yang ada tetap berfungsi dan pagination/sorting tidak memodifikasi query API.
- [x] Tambahkan coverage perilaku sorting/pagination dan visibilitas kolom aksi sesuai role.
- [x] Verifikasi test halaman terkait dan lint frontend.

## Task 3: Migrasikan notifikasi dan roster kelas

**Files:**
- Modify: `frontend/src/features/notifications/NotificationsPage.tsx`
- Modify: `frontend/src/features/classes/Roster.tsx`
- Modify corresponding existing page tests.

**Interfaces:** Gunakan fondasi DataTable dari Task 1. Aksi resend/notifikasi atau pengelolaan roster tetap dipasok melalui kolom aksi milik halaman.

- [x] Petakan kolom sortable secara eksplisit; field pesan error panjang dan email mempertahankan wrapping yang terbaca.
- [x] Pertahankan filter status notifikasi, aksi retry/resend yang ada, dan aturan roster.
- [x] Pastikan tabel lebar responsif dan pagination reset ke halaman valid setelah filter berubah.
- [x] Tambahkan coverage filter, aksi, dan kondisi hasil kosong yang relevan.
- [x] Verifikasi test halaman terkait dan lint frontend.

## Task 4: Pisahkan bagian dashboard

**Files:**
- Create: `frontend/src/features/dashboard/SummaryCards.tsx`
- Create: `frontend/src/features/dashboard/RecentReleases.tsx`
- Modify: `frontend/src/features/dashboard/DashboardPage.tsx`
- Modify: `frontend/src/features/dashboard/api.ts`, dashboard schema/service/repository backend, dan test backend terkait.
- Modify: `frontend/src/features/dashboard/AnalyticsPages.test.tsx` atau test dashboard terkait.

**Interfaces:** Komponen menerima props data eksplisit; query, role lookup, ekspansi course, dan refocus baris tetap dikendalikan `DashboardPage`. Objek `DashboardCourse` menyertakan `created_at`; response mengurutkan mata kuliah terbaru lebih dahulu, dan UI membatasi daftar ke lima.

- [x] Pindahkan render kartu statistik ke `SummaryCards` tanpa mengubah label dan nilai.
- [x] Pindahkan panel rilis ke `RecentReleases` dengan callback untuk membuka course/class.
- [x] Sertakan `created_at` mata kuliah pada endpoint ringkasan dan urutkan daftar menurun berdasarkan waktu pembuatan dengan ID sebagai tie-break stabil; pertahankan hitungan total.
- [x] Tampilkan paling banyak lima mata kuliah terbaru dan tautan â€œLihat semuaâ€ menuju `/courses`.
- [x] Pertahankan aria labels, reduced motion, fokus setelah ekspansi, state loading/error, dan empty state.
- [x] Tambahkan test untuk data role admin/dosen dan aktivasi item rilis yang memanggil callback.
- [x] Verifikasi test dashboard terkait dan lint frontend.

## Task 5: Satukan tampilan info pengguna login

**Files:**
- Create: `frontend/src/components/SessionProfile.tsx`
- Modify: `frontend/src/components/Layout.tsx`
- Modify: `frontend/src/components/Sidebar.tsx`
- Modify/add test layout/auth yang relevan.

**Interfaces:** `SessionProfile` menerima `user: AuthUser` dan `onLogout: () => void`; komponen menampilkan seluruh identitas serta tombol keluar hanya di bawah Sidebar. Layout tetap memiliki efek logout. Sidebar tidak menampilkan Notifikasi; header menampilkan tautan Notifikasi untuk superadmin.

- [x] Pindahkan nama, email, inisial, label peran, dan tombol keluar ke `SessionProfile` yang ditempatkan hanya di dasar Sidebar.
- [x] Pertahankan callback logout di Layout dan sambungkan ke tombol keluar pada profil sidebar.
- [x] Hapus tautan Notifikasi dari Sidebar; tambahkan tautan Notifikasi di sisi kanan header untuk superadmin.
- [x] Pertahankan header responsif, truncation, dan label aksesibel; pastikan tidak ada duplikasi profil sesi.
- [x] Tambahkan test profil sidebar, tautan notifikasi header, dan aksi logout.
- [x] Verifikasi test terkait dan lint frontend.

## Task 6: Integrasi dan validasi cakupan

**Files:** Seluruh file pada Task 1â€“5; referensi seluruh pemakai `components/ui/table.tsx`.

- [x] Periksa semua pemakai tabel: migrasikan hanya daftar data operasional yang disebutkan; pastikan matriks nilai/laporan tetap memakai primitive tabel.
- [x] Pastikan tak ada import atau dependency TanStack Table yang tidak digunakan dan primitive tabel lama tetap kompatibel.
- [x] Jalankan test frontend, `npm run build`, dan `npm run lint` dari `frontend/`.
- [x] Review diff terhadap wireframe, keyboard accessibility, role, state query, dan responsivitas.
