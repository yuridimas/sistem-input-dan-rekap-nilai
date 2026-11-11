# Feature Index Pages Standardization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Complete each task's tests and verification before moving to the next.

**Goal:** Bawa halaman Courses, Students, dan Notifications ke pola index yang sama dengan Users, mengikuti aturan `frontend/src/features/AGENTS.md` dan mempertahankan kontrak serta hak akses tiap fitur.

**Architecture:** Gunakan kembali `DataTable` yang sudah membungkus card, page-size selector, sorting, empty state, dan pagination. Setiap halaman memiliki pencarian `Cari` inline dan refresh di toolbar kanan. Filter status Notifications dipisahkan menjadi card dengan draft state serta aksi Terapkan/Reset; filter tidak mengubah request sampai diterapkan.

**Tech Stack:** React, TypeScript, TanStack Table, TanStack Query, shadcn components di atas Base UI, Vitest, React Testing Library.

**Spec:** `frontend/src/features/AGENTS.md` dan pola yang sudah berjalan di `frontend/src/features/users/UsersPage.tsx`.

## Global Constraints

- Jangan mengubah backend endpoint, schema, atau database untuk pekerjaan ini.
- Pertahankan query/API, permission, aksi domain, empty/loading/error state, dan perilaku dialog yang sudah ada.
- Jangan menambahkan statistik atau filter baru tanpa data/keperluan yang sudah didukung.
- Semua label UI berbahasa Indonesia dan semua aksi ikon memiliki accessible name yang menyebut objeknya.
- `DataTable` mengurus page size di kiri, search dan refresh di kanan, serta pagination bawah; jangan membuat kontrol duplikat.
- Ikuti aturan proporsi kolom dan wrapping sel di `frontend/src/features/AGENTS.md`.

## Review Focus

- Email atau detail panjang tidak boleh meluber ke kolom sebelah; uji sel berisi alamat panjang dan email null.
- Search lokal tidak boleh memicu request baru; filter status Notifications hanya mengirim request setelah Terapkan.
- Refresh harus memanggil `refetch` tanpa menggandakan tombol di header.
- Aksi edit/hapus tetap dibatasi sesuai role dan kepemilikan yang sudah ada.
- Error/loading/empty state harus tetap menampilkan kontrol pencarian dan refresh yang masih dapat dipakai.

---

### Task 1: Standardisasi index Courses

**Files:**
- Modify: `frontend/src/features/courses/CoursesPage.tsx`
- Create: `frontend/src/features/courses/CoursesPage.test.tsx`

**Interfaces:**
- Input data tetap `Course` dari `@/features/academic/api` dan daftar tetap berasal dari `useAcademicQuery<Course[]>("/courses")`.
- Aksi tambah/edit/hapus tetap memakai `CourseDialog`; permission owner/superadmin tidak berubah.

- [ ] **Step 1: Tulis tes halaman Courses**

  Buat harness untuk `CoursesPage` yang memalsukan `useAcademicQuery` dan `useAuth`. Tambahkan tes berikut:

  - `filters courses by name or code through the inline Cari input`: label pencarian bernama `Cari`, label berada sebaris dengan search input, dan mengetik teks menyaring baris tanpa request baru.
  - `refreshes courses from the table toolbar`: tombol `Segarkan` memanggil `refetch` yang dikembalikan query.
  - `keeps create and row actions connected to existing dialogs`: Tambah membuka dialog create; edit/hapus membuka dialog untuk course yang dipilih.
  - `shows edit action in blue and keeps destructive action destructive`: edit memakai aksen biru, hapus memakai destructive, dan visibilitas tetap mengikuti owner/superadmin.

- [ ] **Step 2: Jalankan tes baru dan pastikan gagal pada perbedaan UI saat ini**

  Run: `npm test -- --run src/features/courses/CoursesPage.test.tsx`

  Expected: FAIL karena search belum memakai label/posisi `Cari` inline dan edit belum memakai aksen biru; kegagalan lain hanya jika kontrak halaman yang diuji belum terpenuhi.

- [ ] **Step 3: Sesuaikan CoursesPage**

  Ubah search menjadi label `Cari` inline, pertahankan search domain nama/kode, refresh di slot `actions`, dan beri edit button styling biru dari aturan fitur. Tetapkan ukuran kolom proporsional untuk mata kuliah, semester/SKS, dan tindakan; konten nama/kode harus wrap di dalam kolomnya.

- [ ] **Step 4: Jalankan tes Courses dan periksa hasil**

  Run: `npm test -- --run src/features/courses/CoursesPage.test.tsx`

  Expected: PASS, termasuk permission dan integrasi dialog yang ada.

- [ ] **Step 5: Build dan lint frontend**

  Run dari `frontend/`: `npm run build` dan `npm run lint`

  Expected: kedua perintah berhasil.

- [ ] **Step 6: Commit task Courses**

  ```bash
  git add frontend/src/features/courses/CoursesPage.tsx frontend/src/features/courses/CoursesPage.test.tsx
  git commit -m "feat(courses): align index page with shared table rules"
  ```

### Task 2: Standardisasi index Students

**Files:**
- Modify: `frontend/src/features/students/StudentsPage.tsx`
- Modify: `frontend/src/features/students/StudentsPage.test.tsx`

**Interfaces:**
- Data tetap `Student` dari `@/features/academic/api` dan daftar tetap dimuat oleh `useAcademicQuery<Student[]>("/students")`.
- Mahasiswa dapat ditambah sesuai perilaku yang ada; aksi edit/hapus tetap hanya untuk superadmin.

- [ ] **Step 1: Perluas tes Students sebelum mengubah UI**

  Tambahkan mock `refetch` pada query fixture dan tes berikut:

  - `uses an inline Cari input to search name and NIM`: mencari nama/NIM menyaring baris lokal dan label `Cari` inline dengan input.
  - `refreshes students from the table toolbar`: tombol `Segarkan` memanggil `refetch`.
  - `wraps long and missing student emails inside their cell`: email panjang tetap di kolom email; nilai null menampilkan placeholder tanpa overflow.
  - `styles superadmin edit action blue and preserves lecturer restrictions`: edit biru, hapus destructive, dan dosen tetap tidak melihat aksi edit/hapus.

- [ ] **Step 2: Jalankan tes Students dan konfirmasi kegagalan yang relevan**

  Run: `npm test -- --run src/features/students/StudentsPage.test.tsx`

  Expected: FAIL pada label/posisi search atau style edit; tes permission lama tetap menjadi baseline.

- [ ] **Step 3: Sesuaikan StudentsPage**

  Terapkan search inline berlabel `Cari`, refresh di toolbar kanan, wrapping email dengan `whitespace-normal text-wrap` dan pemecahan kata, serta styling biru untuk edit. Pertahankan ukuran relatif mahasiswa/email/tindakan dan layout saat kolom tindakan tidak dirender.

- [ ] **Step 4: Jalankan tes Students**

  Run: `npm test -- --run src/features/students/StudentsPage.test.tsx`

  Expected: PASS untuk pencarian, wrapping, refresh, dan pembatasan aksi berbasis role.

- [ ] **Step 5: Build dan lint frontend**

  Run dari `frontend/`: `npm run build` dan `npm run lint`

  Expected: kedua perintah berhasil.

- [ ] **Step 6: Commit task Students**

  ```bash
  git add frontend/src/features/students/StudentsPage.tsx frontend/src/features/students/StudentsPage.test.tsx
  git commit -m "feat(students): align index page with shared table rules"
  ```

### Task 3: Standardisasi index Notifications

**Files:**
- Modify: `frontend/src/features/notifications/NotificationsPage.tsx`
- Modify: `frontend/src/features/notifications/NotificationsPage.test.tsx`

**Interfaces:**
- Data tetap dari `GET /admin/notifications`; status server tetap menerima `queued`, `sent`, `failed`, atau tanpa filter.
- Retry tetap `POST /admin/notifications/{id}/retry`; sukses memperbarui cache dan memilih status hasil retry.
- Filter awal tetap `failed` agar halaman audit membuka notifikasi yang memerlukan tindakan.

- [ ] **Step 1: Ubah tes agar mensyaratkan filter Apply/Reset dan search lokal**

  Perbarui `filters statuses and retries a failed notification` agar perubahan status draft tidak mengubah `api.get` sebelum klik Terapkan. Setelah Terapkan, pastikan query memakai status terpilih. Klik Reset harus mengembalikan draft dan query aktif ke `failed`. Tambahkan tes `searches notification email and error text locally` yang memastikan input `Cari` menyaring hasil tanpa request API tambahan. Tambahkan tes refresh toolbar memanggil `query.refetch`.

- [ ] **Step 2: Jalankan tes Notifications dan pastikan gagal pada perilaku yang belum ada**

  Run: `npm test -- --run src/features/notifications/NotificationsPage.test.tsx`

  Expected: FAIL karena filter status saat ini langsung mengirim request, belum ada search, dan filter masih di toolbar tabel.

- [ ] **Step 3: Pindahkan filter status ke card filter terpisah**

  Simpan `draftFilter` terpisah dari `filter` aktif. Terapkan filter hanya melalui submit form; Reset mengembalikan keduanya ke `failed`. Saat retry sukses, sinkronkan nilai aktif dan draft ke status hasil retry supaya tampilan tetap konsisten.

- [ ] **Step 4: Tambahkan search inline dan rapikan toolbar tabel**

  Tambahkan search lokal berlabel `Cari` yang mencocokkan email, status, dan detail error; jangan ubah query key saat mengetik. Pindahkan refresh ke slot `actions`. Hapus hitungan notifikasi dari slot toolbar karena informasi jumlah baris sudah disediakan pagination. Jangan tambahkan kartu statistik: endpoint yang sedang dipakai hanya menyediakan hasil sesuai status aktif, bukan agregat lintas status.

- [ ] **Step 5: Verifikasi status filter, retry, search, dan akses**

  Run: `npm test -- --run src/features/notifications/NotificationsPage.test.tsx`

  Expected: PASS untuk Apply/Reset, retry sukses/gagal, pencarian lokal, sorting, dan guard role superadmin.

- [ ] **Step 6: Build dan lint frontend**

  Run dari `frontend/`: `npm run build` dan `npm run lint`

  Expected: kedua perintah berhasil.

- [ ] **Step 7: Commit task Notifications**

  ```bash
  git add frontend/src/features/notifications/NotificationsPage.tsx frontend/src/features/notifications/NotificationsPage.test.tsx
  git commit -m "feat(notifications): align index page with shared table rules"
  ```

### Final verification

- [ ] Jalankan seluruh tes frontend: `npm test` dari `frontend/`; semua tes lulus.
- [ ] Jalankan `npm run build` dan `npm run lint`; keduanya berhasil.
- [ ] Periksa diff akhir untuk memastikan tidak ada endpoint/backend change, aksi yang tidak didukung, atau file di luar tiga halaman dan tesnya.
- [ ] Uji `/courses`, `/students`, dan `/notifications` di browser untuk posisi toolbar, wrap kolom, filter status, loading/error/empty state, dan aksi berbasis role.
