# Halaman Pengguna Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ganti placeholder menu Pengguna dengan daftar akun yang dapat ditinjau superadmin untuk membantu uji manual.

**Architecture:** Gunakan endpoint `GET /admin/users` yang sudah ada melalui shared Axios client dan React Query. Filter peran/status dikirim ke backend, sedangkan pencarian nama/email diterapkan pada hasil; route dan sidebar tetap superadmin-only.

**Tech Stack:** React, TypeScript, TanStack React Query, Axios shared client, komponen UI repository, Vitest, React Testing Library.

**Spec:** `docs/superpowers/specs/2026-11-05-users-page-design.md`

## Global Constraints

- Implementasi hanya daftar akun; tidak membuat, mengubah, atau menonaktifkan akun.
- Jangan menampilkan password, password hash, atau token.
- Pertahankan role guard superadmin dan gunakan pola query/error/table yang sudah ada.
- Jangan menambah API/backend atau dependency baru.

## Review Focus

- Query role/status membentuk request dan cache key yang sesuai sehingga filter tidak menampilkan hasil stale.
- Pencarian tidak peka kapitalisasi dan mencocokkan nama maupun email.
- Loading, error/retry, hasil kosong, dan hasil berisi dapat dibedakan dengan aksesibilitas yang layak.
- Lecturer/student yang membuka route secara langsung tetap ditolak oleh `ProtectedRoute`.
- Kredensial rahasia tidak pernah menjadi kolom atau bagian render.

---

### Task 1: Implementasikan halaman daftar pengguna

**Files:**
- Create: `frontend/src/features/users/UsersPage.tsx`
- Modify: `frontend/src/App.tsx`
- Test: `frontend/src/features/users/UsersPage.test.tsx`

**Interfaces:**
- `UsersPage` mengambil `UserRead[]` dengan field `id`, `email`, `full_name`, `role`, `is_active`, `created_at`, `updated_at` dari `/admin/users`.
- Query key memuat filter role/status; pencarian lokal tidak mengubah request.

- [x] Tambahkan test render daftar (nama, email, role, active, created date), filter role/status, dan pencarian nama/email.
- [x] Tambahkan test loading, error dengan aksi retry, empty state, dan kegagalan API yang terformat.
- [x] Jalankan `npm test -- --run src/features/users/UsersPage.test.tsx` dari `frontend/` untuk melihat test gagal sebelum implementasi.
- [x] Buat halaman mengikuti pola `NotificationsPage`, `PageHeader`, `QueryState`, `NativeSelect`, `Table`, dan `Badge`; sediakan tombol refresh.
- [x] Ganti placeholder route `/users` dengan lazy import `UsersPage` sambil mempertahankan wrapper `ProtectedRoute` role superadmin.
- [x] Jalankan test halaman dan test route/auth yang relevan.

### Task 2: Verifikasi akses dan kualitas frontend

**Files:**
- Modify if needed: `frontend/src/features/users/UsersPage.tsx`
- Test: `frontend/src/features/users/UsersPage.test.tsx`
- Reference: `frontend/src/components/Sidebar.tsx`, `frontend/src/App.tsx`

- [x] Pastikan link Pengguna tetap hanya terlihat bagi superadmin dan direct navigation role lain ditolak; tambahkan coverage pada test route/auth yang sudah ada bila belum tercakup.
- [x] Pastikan render tidak membaca/menampilkan field selain kontrak `UserRead`.
- [x] Jalankan `npm test -- --run`, `npm run build`, dan `npm run lint` dari `frontend/`.
- [x] Review diff agar perubahan tetap read-only dan tidak mencakup CRUD atau password.
