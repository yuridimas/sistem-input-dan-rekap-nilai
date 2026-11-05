# Desain halaman Pengguna

**Status:** Disetujui dan diimplementasikan melalui plan halaman Pengguna.
**Tanggal:** 2026-11-05.
**Keputusan pengguna:** Implementasikan daftar akun saja.

## Tujuan

Superadmin dapat melihat akun yang tersedia dari menu Pengguna tanpa perlu mengetahui route API. Daftar membantu human menemukan email dan peran akun untuk uji manual. Backend `GET /admin/users` sudah tersedia dengan filter peran dan status aktif; halaman frontend saat ini masih placeholder.

## Pendekatan

| Pendekatan | Pertimbangan | Keputusan |
| --- | --- | --- |
| Daftar akun dengan filter server dan pencarian lokal | Menggunakan endpoint serta pola React Query yang sudah ada, cakupan kecil, dan langsung menjawab kebutuhan menemukan akun | Dipilih |
| CRUD akun lengkap | Endpoint backend tersedia, tetapi form password, validasi, konflik email, dan deaktivasi memperluas alur di luar kebutuhan daftar akun | Tidak dipilih |

## Perilaku halaman

- Route tetap `/users`, hanya dapat diakses superadmin, dan memuat halaman secara lazy seperti fitur frontend lain.
- Kolom tabel: nama lengkap, email, peran, status aktif, dan waktu dibuat. Filter peran dan status memakai query params backend; pencarian nama/email dilakukan lokal atas hasil filter.
- Tampilkan loading, error dengan aksi coba lagi, empty state, jumlah hasil, dan aksi refresh dengan pola komponen UI yang sudah ada.
- Gunakan shared Axios client dan React Query. Jangan buat endpoint atau dependency baru.
- Jangan pernah menampilkan password, hash, atau token. Password akun seed tidak dapat dibaca balik; petunjuk kredensial seed tetap berada pada dokumentasi seeding/environment.
- Tetap menjaga akses menu/route berdasarkan role dan menambahkan coverage komponen untuk filter, pencarian, state query, dan pembatasan route.

## Batasan

Tidak mencakup create/edit/deactivate akun, pagination backend, perubahan schema/API, ataupun pengungkapan password akun. Untuk daftar yang tersedia, jumlah pengguna saat ini dimuat dari endpoint existing.
