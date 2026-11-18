# Pengembangan Frontend

Frontend memakai React, TypeScript, Vite, TanStack Query/Table, Axios, Zustand, Tailwind, Recharts, dan komponen shadcn/Base UI.

Untuk stack Docker lengkap, ikuti [README utama](../README.md). Panduan ini menjalankan Vite langsung di host dan memakai API yang sudah berjalan.

## Dokumentasi

| Panduan | Isi |
| --- | --- |
| [Arsitektur](../docs/architecture.md) | State browser, API, dan alur penilaian |
| [Struktur repository](../docs/structure.md) | Pembagian features, komponen bersama, dan utilitas |
| [Instalasi](../docs/installation.md) | Runtime, environment, serta port Docker/host |
| [Penggunaan](../docs/usage.md) | Alur akun, mata kuliah, kelas, nilai, dan laporan |
| [API](../docs/api.md) | Kontrak endpoint yang dipakai frontend |
| [Testing](../docs/testing.md) | Vitest, TypeScript build, dan Oxlint |

## Arsitektur dan fitur

`src/App.tsx` merangkai router, TanStack Query, halaman lazy, dan route guard. Shared Axios client memasang bearer token serta mengoordinasikan refresh sesi; Zustand menyimpan token dan hidrasi profil. Engine draft nilai menyimpan edit yang belum selesai terpisah dari snapshot server agar pergantian tab kelas tidak membuang input.

| Halaman | Perilaku utama |
| --- | --- |
| `/dashboard` | Ringkasan mata kuliah/kelas, rilis tertunda, dan rilis terbaru dalam lingkup pengguna |
| `/courses`, `/courses/:courseId` | Index mata kuliah dan tabel kelas; pencarian lokal serta aksi pengelolaan sesuai akses |
| `/classes/:classId` | Roster, komponen penilaian, grid nilai, dan analisis |
| `/students`, `/students/:studentId` | Direktori mahasiswa dan riwayat hasil final |
| `/users` | Superadmin: daftar/summary akun, create/edit, perubahan password opsional, dan deactivation |
| `/notifications` | Superadmin: audit notifikasi dan retry record failed |

Tabel index memakai wrapper `DataTable` berbasis TanStack Table untuk sorting dan pagination lokal, dengan pilihan 10/25/50 baris. Server masih mengembalikan array hasil filter; pagination tidak membatasi jumlah record yang diunduh. Filter peran/status pengguna dan status notifikasi baru dikirim setelah **Terapkan**; **Reset** mengembalikan nilai awal. Pencarian lokal bekerja pada hasil yang sudah diambil. Kartu summary pengguna menghitung hasil filter server sebelum pencarian lokal.

Breadcrumbs menjaga konteks mata kuliah/kelas. Navigasi mata kuliah tetap aktif saat membuka detail kelas. Superadmin membuka Notifikasi melalui ikon bell pada header; profil sesi dan **Keluar** berada di bagian bawah sidebar. Pembatasan UI melengkapi pemeriksaan otorisasi di backend.

## Setup di host

Gunakan Node.js yang memenuhi `^22.22.2 || ^24.15.0 || >=26.0.0`, sesuai [`package.json`](package.json). Perintah berikut memakai PowerShell.

Vite di host memakai port 5173, sedangkan frontend Docker dipublikasikan pada 15173. Keduanya dapat berjalan bersamaan.

Dari **root repository**, masuk ke frontend dan instal dependency berdasarkan lock file:

```powershell
cd frontend
npm ci
```

Buat `frontend/.env.local` berisi URL API yang dapat dijangkau browser:

```dotenv
VITE_API_URL=http://localhost:18000
```

Contoh tersebut mengakses API Docker. Jika memakai API native, gunakan `http://localhost:8000`. Kemudian, dari **`frontend/`**:

```powershell
npm run dev
```

Buka <http://localhost:5173>. Restart Vite setelah mengubah environment. Variabel `VITE_*` masuk ke bundle browser; jangan gunakan untuk secret.

## Menambah atau mengubah fitur

| Lokasi | Penggunaan |
| --- | --- |
| `src/features/` | Halaman, hooks, dan logic yang dimiliki fitur |
| `src/features/academic/api.ts` | Kontrak dan hooks query/mutation akademik dengan cache per pengguna |
| `src/features/users/` | Daftar/summary akun, types, serta dialog create/edit/deactivate |
| `src/lib/api.ts` | Client Axios bersama dengan bearer token dan refresh sesi |
| `src/lib/navigation.ts` | Label navigasi dan status aktif konteks mata kuliah/kelas |
| `src/stores/` | State Zustand, termasuk token dan hidrasi sesi |
| `src/components/` | Layout, navigasi, dan komponen bersama |
| `src/components/data-table/` | Wrapper tabel, toolbar, sorting, pagination, dan empty state |
| `src/components/ui/` | Primitive UI dari shadcn/Base UI |
| `src/App.tsx` | Route, provider React Query, dan guard halaman |

Gunakan import `@/` untuk modul sumber dan client API bersama agar request mengikuti mekanisme sesi. Setelah mutation, invalidasi query yang terdampak. Untuk input nilai, pertahankan state draft pada engine/hook di `src/features/grades/` agar perubahan tab tidak membuang edit lokal.

Dokumentasikan kontrak fungsi/type menggunakan JSDoc/TSDoc. Gunakan komentar `//` untuk alasan logic yang tidak langsung jelas.

Untuk halaman index, ikuti [aturan fitur](src/features/AGENTS.md): gunakan `PageHeader` dan `DataTable`, tempatkan filter dalam satu card, pisahkan pilihan draft dari filter aktif, dan sediakan label aksesibel pada tombol ikon. Pertahankan loading/error serta kontrol pencarian/filter yang masih berguna.

## Test, build, dan lint

Jalankan dari **`frontend/` menggunakan PowerShell**:

```powershell
npm test
npm test -- src/features/grades/draft.test.ts
npm test -- src/features/users/UsersPage.test.tsx
npm test -- src/components/data-table/DataTable.test.tsx
npm run build
npm run lint
```

Vitest memakai jsdom dan React Testing Library. Tests yang ada memakai API mock sehingga tidak membutuhkan database backend. `npm run build` menjalankan TypeScript check sebelum menghasilkan `dist/`; `npm run lint` menjalankan Oxlint.

Cakupan tests meliputi draft/grid nilai, analytics, users/dialog/filter, notifikasi, courses/classes, roster, direktori mahasiswa, dashboard, navigasi/layout, shared tables, dan download. Manifest belum menetapkan coverage threshold atau script coverage. Jalankan npm dari `frontend/`; root `package.json` tidak menyediakan runner tests aplikasi.

Untuk memeriksa bundle secara lokal, jalankan dari **`frontend/` menggunakan PowerShell**:

```powershell
npm run preview
```

Gunakan URL yang dicetak Vite. Preview hanya melayani frontend; API tetap harus tersedia.

## Build deployment

[`Dockerfile.prod`](Dockerfile.prod) membangun bundle lalu melayaninya melalui Nginx. Compose memasok build arg `VITE_API_URL=/api`; proxy deployment meneruskan prefix tersebut ke backend.

URL API ditetapkan saat build. Mengubah environment container Nginx setelah build tidak mengganti URL dalam bundle. Ikuti [panduan deployment](../docs/deployment.md) untuk membangun dan memeriksa stack.

## Troubleshooting

| Gejala | Pemeriksaan |
| --- | --- |
| Request menuju API yang salah | Periksa `VITE_API_URL`, restart Vite, atau rebuild bundle deployment. |
| Error CORS | Cocokkan origin browser dengan `CORS_ORIGINS` pada backend. |
| Port 5173 terpakai | Periksa proses native lain atau jalankan Vite dengan `npm run dev -- --port 5174`, lalu sesuaikan `CORS_ORIGINS` backend. Frontend Docker memakai port host 15173. |
| Error versi Node atau instalasi | Cocokkan versi dengan `engines`, lalu jalankan `npm ci`. |
