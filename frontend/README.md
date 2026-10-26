# Development Frontend

Frontend memakai React, TypeScript, Vite, React Query, Zustand, Tailwind, dan komponen shadcn/Base UI.

Untuk stack Docker lengkap, ikuti [README utama](../README.md). Panduan ini menjalankan Vite langsung di host dan memakai API yang sudah berjalan.

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
| `src/lib/api.ts` | Client Axios bersama dengan bearer token dan refresh sesi |
| `src/stores/` | State Zustand, termasuk token dan hidrasi sesi |
| `src/components/` | Layout, navigasi, dan komponen bersama |
| `src/components/ui/` | Primitive UI dari shadcn/Base UI |
| `src/App.tsx` | Route, provider React Query, dan guard halaman |

Gunakan import `@/` untuk modul sumber dan client API bersama agar request mengikuti mekanisme sesi. Setelah mutation, invalidasi query yang terdampak. Untuk input nilai, pertahankan state draft pada engine/hook di `src/features/grades/` agar perubahan tab tidak membuang edit lokal.

Dokumentasikan kontrak fungsi/type menggunakan JSDoc/TSDoc. Gunakan komentar `//` untuk alasan logic yang tidak langsung jelas.

## Test, build, dan lint

Jalankan dari **`frontend/` menggunakan PowerShell**:

```powershell
npm test
npm test -- src/features/grades/draft.test.ts
npm run build
npm run lint
```

Vitest memakai jsdom dan React Testing Library. Tests yang ada memakai API mock sehingga tidak membutuhkan database backend. `npm run build` menjalankan TypeScript check sebelum menghasilkan `dist/`; `npm run lint` menjalankan Oxlint.

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
