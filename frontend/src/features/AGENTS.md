# Aturan Halaman Index Fitur

Berlaku untuk halaman daftar/index di bawah `frontend/src/features/`. Ikuti pola ini untuk courses, students, users, notifications, dan fitur serupa. Terapkan hanya bagian yang didukung kebutuhan halaman dan API yang ada.

## Susunan halaman

- Gunakan `PageHeader` dari `@/features/academic/Management` dengan judul dan deskripsi berbahasa Indonesia. Tampilkan aksi yang benar-benar tersedia: misalnya tambah bila endpoint create ada; jangan menambahkan export, detail, atau aksi lain tanpa dukungan nyata.
- Tampilkan kartu statistik hanya bila metriknya relevan dan bisa dihitung dari data yang tersedia. Kelompokkan metrik secara jelas dan jangan membuat hitungan berubah hanya karena pencarian lokal kecuali memang itu perilaku yang diminta.
- Jika halaman memiliki filter, letakkan semua filter dalam satu card terpisah di atas tabel. Gunakan tombol **Terapkan** dan **Reset**; perubahan pilihan draft tidak mengirim request sampai diterapkan. Reset mengembalikan pilihan draft dan filter aktif ke nilai awal.
- Gunakan `DataTable` dari `@/components/data-table` untuk card tabel. Komponen ini sudah membungkus card, toolbar atas, isi tabel, dan pagination; jangan membuat wrapper card atau pagination duplikat.

## Toolbar dan tabel

- Biarkan pilihan jumlah baris bawaan `DataTable` di sisi kiri toolbar.
- Letakkan pencarian di sisi kanan, inline dengan input `type="search"`. Label singkat dan aksesibel adalah **Cari**; tombol refresh berada sejajar di kanan input.
- Berikan jarak dan padding yang cukup antara toolbar dan isi tabel; gunakan slot `search` dan `actions` pada `DataTable`.
- Buat kolom dengan `ColumnDef<TData>[]` bertipe. Atur `size` secara proporsional; ukuran akan dinormalisasi terhadap kolom yang terlihat. Tinjau ulang proporsi saat kolom aksi disembunyikan berdasarkan role atau status.
- Bungkus teks panjang seperti email di dalam sel dengan `whitespace-normal text-wrap` dan pemecahan kata yang sesuai, agar teks tidak masuk ke kolom berikutnya. `TableCell` bawaan memakai `whitespace-nowrap`, jadi aturan wrapping perlu diberikan pada konten sel.
- Semua tombol pada kolom tindakan memakai ikon yang sesuai dan nama aksesibel spesifik, misalnya `Edit {nama}` atau `Nonaktifkan {nama}`. Gunakan aksen biru untuk edit dan warna destructive untuk tindakan nonaktif/hapus.
- Pertahankan sorting, empty state, loading, dan error state yang sudah disediakan komponen atau pola halaman. Loading/error tidak boleh menghilangkan kontrol filter/pencarian yang masih berguna.

## Data, aksi, dan aksesibilitas

- Cocokkan kolom, filter, statistik, dan aksi dengan response serta endpoint aktual. Jangan mengasumsikan field, endpoint, export, atau operasi CRUD yang tidak tersedia.
- Untuk create/edit/deactivate, validasi payload sesuai schema backend, tampilkan error field, dan invalidate query yang relevan setelah sukses.
- Gunakan label form yang terhubung melalui `htmlFor`, `aria-label` untuk tombol ikon, `aria-live="polite"` untuk informasi dinamis, serta teks UI Bahasa Indonesia.
- Pertahankan authorization berdasarkan role di UI sebagai pelengkap otorisasi server; server tetap menjadi sumber keputusan akses.

## Pemeriksaan

- Untuk perubahan halaman, jalankan tes fitur terkait, `npm run build`, dan `npm run lint` dari `frontend/`.
- Saat memeriksa tabel, verifikasi lebar kolom, wrapping email/teks panjang, posisi toolbar, label aksesibel, filter, serta aksi pada data kosong dan data berisi.
