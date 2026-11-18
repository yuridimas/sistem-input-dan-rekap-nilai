# Panduan penggunaan

Panduan ini mengasumsikan aplikasi sudah berjalan; lihat [instalasi](installation.md). Label antarmuka memakai bahasa Indonesia. [Contoh API](api.md) menjelaskan penggunaan melalui program.

## Login dan persiapan akun

1. Buka <http://localhost:15173> untuk Docker lokal.
2. Login menggunakan email/password bootstrap yang dikonfigurasi.
3. Sebagai superadmin, buka **Pengguna** (`/users`) untuk membuat akun dosen atau memeriksa akun existing. Operasi akun yang sama tersedia melalui `/admin/users` pada [referensi API](api.md).

Dashboard merangkum mata kuliah/kelas yang dapat diakses, rilis tertunda, dan rilis terbaru. Dosen melihat kelas yang ditugaskan kepadanya; superadmin melihat seluruh kelas. Mahasiswa merupakan profil/penerima, bukan role login aplikasi.

## Mengelola pengguna

Hanya superadmin yang dapat membuka **Pengguna**. Tabel menampilkan nama, email, role, status aktif, tanggal dibuat, serta tindakan per baris. Pencarian lokal mencocokkan nama/email tanpa membedakan huruf besar/kecil. Pilih role/status lalu klik **Terapkan** untuk menggunakan filter server; **Reset** mengembalikan semua role/status. Kartu ringkasan menghitung daftar hasil filter server sebelum pencarian lokal.

Gunakan **Tambah pengguna** untuk memasukkan nama, email, password, dan role. Tindakan edit memperbarui profil, role, status aktif, atau password; kosongkan password opsional agar password lama tetap digunakan. **Nonaktifkan** meminta konfirmasi dan menonaktifkan akun aktif sambil mempertahankan record serta history. Password/hash existing tidak ditampilkan. Akun nonaktif tidak dapat login atau melanjutkan operasi API terproteksi.

Tabel daftar mendukung kolom yang dapat diurutkan serta pagination lokal 10/25/50 row per halaman. Pagination mengubah bagian data hasil fetch yang terlihat, tanpa meminta halaman baru ke backend. Identitas sesi dan **Keluar** berada di bagian bawah sidebar.

## Menyiapkan mata kuliah dan kelas

1. Buka **Semua Mata Kuliah** sebagai superadmin atau **Mata Kuliah Saya** sebagai dosen (`/courses`). Cari kode/nama atau buat mata kuliah dengan kode, nama, SKS, dan semester.
2. Buka tindakan lihat mata kuliah untuk memeriksa kelasnya. Cari section/tahun, lihat status penguncian roster, atau buat kelas dengan section dan tahun akademik.
3. Sebagai superadmin, pilih dosen aktif. Sebagai dosen, kelas ditugaskan ke akun sendiri.
4. Buka `/classes/:classId` dan tab **Mahasiswa**, **Komponen Penilaian**, **Nilai**, serta **Analisis**.

Dosen dapat melihat mata kuliah yang dibuatnya atau yang diajarnya melalui kelas. Perubahan/penghapusan metadata mata kuliah memerlukan pembuatnya atau superadmin. Pengelolaan kelas dibatasi pada dosen pengampu atau superadmin.

Breadcrumb menghubungkan kelas dengan mata kuliah dan indeks mata kuliah. Dashboard menampilkan maksimal lima entri mata kuliah; **Lihat semua** membuka indeks jika jumlahnya lebih banyak. Tindakan pada rilis terbaru memfokuskan baris course/class terkait di dashboard.

## Mengisi roster

Pada **Mahasiswa**, daftarkan NIM dengan nama dan email opsional. NIM existing memakai profil mahasiswa yang tersimpan. Isi nama untuk mahasiswa baru; API memakai NIM sebagai fallback jika nama tidak diberikan. Enrollment duplikat menghasilkan konflik.

Direktori global `/students` mendukung pembuatan/pembacaan bagi kedua role; update/delete memerlukan superadmin. Profil yang masih terdaftar pada kelas tidak dapat dihapus. Penghapusan enrollment juga dapat ditolak jika sudah memiliki dependensi penilaian.

Pencarian direktori mencocokkan nama/NIM, sedangkan roster kelas mencocokkan nama/NIM/email. Link mahasiswa membuka history nilai yang telah dirilis. Roster terkunci menonaktifkan penambahan dan menyembunyikan penghapusan; menghapus enrollment berbeda dari menghapus profil mahasiswa global.

Email opsional untuk input akademik, tetapi penerima kosong/tidak valid menghalangi keberhasilan pengiriman. Setelah admin memperbaiki email profil, retry notifikasi yang belum terkirim untuk memperbarui penerimanya.

## Mengatur komponen penilaian

Pada **Komponen Penilaian**, isi nama, kategori, bobot, skor maksimum, serta urutan tampilan, lalu simpan konfigurasi.

| Contoh | Kategori | Bobot | Maksimum |
| --- | --- | --- | --- |
| Tugas | `tugas` | 20 | 100 |
| Ujian tengah semester | `uts` | 30 | 100 |
| Ujian akhir semester | `uas` | 50 | 100 |

Bobot harus tepat 100% dan memiliki minimal satu UTS serta satu UAS. Bobot/maksimum positif dengan maksimal dua desimal. Komponen yang memiliki skor tidak dapat dihapus atau diturunkan maksimumnya di bawah skor tersimpan. Perubahan konfigurasi yang valid menghitung ulang total draft.

## Mengisi dan menyimpan nilai

1. Buka **Nilai** dan isi skor setiap komponen mahasiswa.
2. Perhatikan status save dan selesaikan error validasi/koneksi sebelum meninggalkan halaman.
3. Gunakan kontrol save/retry jika request gagal. Edit draft bertahan saat berpindah tab kelas; navigation guard menangani pekerjaan yang belum selesai.
4. Periksa total dan lengkapi setiap komponen kosong sebelum rilis.

Total menggunakan `sum(score / maximum * weight)`, dibulatkan half-up ke dua desimal. Pada contoh konfigurasi, skor 80, 75, 90 menghasilkan `83.50`. Skor draft yang belum ada berkontribusi nol tanpa pembagian ulang bobot. Sel kosong menghalangi rilis, sedangkan nol tersimpan berarti lengkap. API `null` menghapus skor; ID komponen yang dihilangkan dari payload mempertahankan nilainya.

Edit tertunda disimpan dalam memori. Tunggu save berhasil sebelum reload/keluar. Jika perubahan konfigurasi server menjeda editor, gunakan kontrol reload untuk rekonsiliasi; reload eksplisit membuang draft lokal.

## Memfinalisasi kelas

1. Periksa roster dan komponen.
2. Simpan seluruh skor, termasuk nol eksplisit jika sesuai.
3. Mulai finalisasi; UI menyelesaikan save dan memperbarui snapshot sebelum konfirmasi.
4. Tinjau konfirmasi lalu rilis.
5. Periksa hasil rilis dan jumlah task antrean.

Rilis memerlukan roster berisi mahasiswa, konfigurasi valid, dan skor lengkap dalam rentang. Rilis mengunci edit skor serta perubahan roster/komponen. Aplikasi saat ini tidak menyediakan alur unfinalize.

Jumlah rilis menunjukkan mahasiswa final dan task yang diterima antrean, bukan email yang diterima. Kegagalan broker dapat meninggalkan nilai final dengan notifikasi gagal. Setelah timeout yang hasilnya tidak pasti, periksa status server sebelum retry; rilis ulang menghasilkan konflik.

## Analisis dan laporan

Gunakan **Analisis** untuk chart/ranking kelas. Ranking disimpan saat rilis; skor seri diurutkan menurut NIM/nama dengan posisi berbeda.

Buka `/students/:studentId` untuk history/trend rilis sesuai cakupan akses. Draft tidak muncul di history rilis. Download PDF individu memakai ID enrollment, bukan ID profil mahasiswa global.

Kelas yang dirilis menyediakan kontrol PDF/XLSX. PDF individu memerlukan nilai enrollment final; ekspor kelas memerlukan seluruh nilai roster final. XLSX berisi skor komponen, total, ranking, serta label lulus/tidak lulus dengan ambang 45. Isi `INSTITUTION_NAME` untuk identitas laporan.

## Notifikasi

Sebagai superadmin, gunakan ikon bell pada header untuk membuka **Notifikasi** (`/notifications`). Pilih `queued`, `sent`, atau `failed`, lalu klik **Terapkan**; **Reset** mengembalikan filter notifikasi gagal. Cari penerima/status/error secara lokal. Tindakan retry muncul pada baris gagal; perbaiki penerima/broker/worker/SMTP sebelum mencoba lagi. API juga mendukung retry status lain yang belum terkirim, sedangkan record `sent` menolak retry.

`SMTP_HOST` kosong berarti mock transport: logging dapat menghasilkan `sent` tanpa menghubungi SMTP. Email nyata memerlukan konfigurasi SMTP dan worker dengan database/Redis yang sama seperti API.

## Menelusuri kasus dari seeder

Gunakan [panduan seeding](seeding.md) untuk mata kuliah/kelas berisi data dan beberapa sample per kasus positif/negatif. Manifest menyediakan email aktor, path/payload, expected status, serta ID target course/class/student/enrollment. Ketiga aktor memakai password yang diberikan saat dataset dibuat; dua aktor merupakan dosen, termasuk dosen pembanding untuk pemeriksaan penolakan akses. Superadmin dapat melihat akun pada **Pengguna**.

Sample profile `manual` memakai target mahasiswa berbeda dalam kelas setiap kasus; setiap sample finalisasi sukses memiliki kelas sendiri. Aksi tulis mengubah prasyarat sehingga skenario awal yang segar memerlukan nama dataset baru. Apply ulang mempertahankan edit human. Profile `light-load` menyediakan data dan target berbatas untuk request berulang; penjadwalan load/concurrency ditentukan pemanggil.

## Masalah umum

| Gejala | Tindakan |
| --- | --- |
| Password seed berubah tetapi login tetap sama | Seed tidak mereset akun; gunakan API update akun dengan otorisasi yang sesuai. |
| Konfigurasi/save ditolak | Periksa total bobot 100%, UTS/UAS, maksimum positif, dan rentang skor. |
| Sel kosong menghalangi rilis | Isi sel yang disebutkan; kosong berbeda dari nol. |
| Operasi tulis menghasilkan 409 | Reload; data mungkin sudah final, duplikat, atau dilindungi dependensi. |
| Hasil rilis tidak pasti | Periksa status server sebelum retry. |
| Laporan menghasilkan 409 | Pastikan nilai enrollment/seluruh roster final. |
| PDF menghasilkan 503 | Gunakan image backend yang memiliki library/font renderer. |
| Email masih queued/failed | Periksa worker, broker, penerima, SMTP, lalu retry sebagai admin. |
| URL API browser salah | Perbaiki `VITE_API_URL`, restart/rebuild, dan periksa CORS. |
| Nama/fingerprint seed konflik | Gunakan nama dataset baru untuk konfigurasi seed/profile/generator yang berubah. |
