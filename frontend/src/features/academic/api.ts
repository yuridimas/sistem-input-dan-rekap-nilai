/**
 * Kontrak akademik dan adapter React Query bersama bagi halaman pengelolaan.
 * Cache dipisahkan per pengguna; mutasi menyegarkan ringkasan yang terpengaruh.
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";

import api from "@/lib/api";
import { useAuth } from "@/features/auth/useAuth";

/**
 * Metadata mata kuliah; created_by dipakai UI untuk membedakan hak baca dan hak ubah.
 */
export interface Course {
  id: string;
  code: string;
  name: string;
  credits: number;
  semester: string;
  created_by: string;
}
/**
 * Metadata kelas dan penanda penguncian finalisasi yang dihitung backend.
 */
export interface AcademicClass {
  id: string;
  course_id: string;
  section: string;
  academic_year: string;
  lecturer_id: string;
  has_finalized_grades: boolean;
}
/**
 * Profil global mahasiswa; email null berarti belum ada tujuan notifikasi.
 */
export interface Student {
  id: string;
  nim: string;
  full_name: string;
  email: string | null;
}
/**
 * ID keikutsertaan dipisahkan dari ID profil untuk endpoint penilaian/enrollment.
 */
export interface RosterEntry {
  id: string;
  student: Student;
}
/**
 * Pilihan penugasan kelas dari daftar akun dosen administratif.
 */
export interface Lecturer {
  id: string;
  full_name: string;
  email: string;
  is_active: boolean;
}
/**
 * Konfigurasi kolom penilaian; Decimal weight/max_score tetap string dari API.
 */
export interface GradeComponent {
  id: string;
  name: string;
  category: "tugas" | "uts" | "uas" | "custom";
  weight: string;
  max_score: string;
  order_index: number;
}

/**
 * Muat path akademik dengan cache terpisah berdasarkan identitas pengguna.
 * @param path Path relatif API; enabled menahan query sampai konteks siap.
 * @returns Hasil useQuery<T>; error ditampilkan pemanggil, retry otomatis dinonaktifkan.
 */
export function useAcademicQuery<T>(path: string, enabled = true) {
  const { user } = useAuth();
  return useQuery({
    queryKey: ["academic", user?.id, path],
    queryFn: async () => (await api.get<T>(path)).data,
    enabled: Boolean(user) && enabled,
    retry: false,
  });
}

/**
 * Jalankan adapter write lalu segarkan cache akademik dan dashboard pengguna.
 * @param write Operasi HTTP; onSuccess opsional berjalan sesudah invalidasi.
 * @returns Hasil useMutation; konflik akses/data menyegarkan cache untuk rekonsiliasi UI.
 */
export function useAcademicMutation<T = void>(
  write: (payload: T) => Promise<unknown>,
  onSuccess?: () => void,
) {
  const client = useQueryClient();
  const { user } = useAuth();
  return useMutation({
    mutationFn: write,
    onSuccess: async () => {
      await Promise.all([
        client.invalidateQueries({ queryKey: ["academic", user?.id] }),
        client.invalidateQueries({
          queryKey: ["dashboard", "summary", user?.id],
        }),
      ]);
      onSuccess?.();
    },
    onError: async (error) => {
      if (
        axios.isAxiosError(error) &&
        [403, 404, 409].includes(error.response?.status ?? 0)
      ) {
        await client.invalidateQueries({ queryKey: ["academic", user?.id] });
      }
    },
  });
}

/**
 * Petakan detail validasi Pydantic ke field form berdasarkan elemen loc terakhir.
 * @returns Pesan string atau undefined jika error bukan validasi field tersebut.
 */
export function fieldError(error: unknown, name: string): string | undefined {
  if (!axios.isAxiosError(error)) return;
  const detail = error.response?.data?.detail;
  if (!Array.isArray(detail)) return;
  const item = detail.find((row) => row.loc?.at(-1) === name);
  if (!item) return;
  return item.type === "value_error"
    ? item.msg.replace(/^Value error, /, "")
    : "Periksa nilai pada kolom ini.";
}

/**
 * Ubah error HTTP/domain menjadi pesan bersama tanpa mengekspos objek error mentah.
 * @returns Pesan string untuk akses, validasi, atau koneksi; tidak mengubah state.
 */
export function errorMessage(error: unknown): string {
  if (!axios.isAxiosError(error))
    return "Terjadi kesalahan. Silakan coba lagi.";
  if (error.response?.status === 403)
    return "Anda tidak memiliki izin untuk tindakan ini.";
  if (error.response?.status === 404)
    return "Data tidak ditemukan atau sudah dihapus.";
  if (error.response?.status === 401)
    return "Sesi berakhir. Silakan masuk kembali.";
  const detail = error.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return "Periksa kembali data yang diisi sebelum menyimpan.";
  return "Tidak dapat menghubungi server. Periksa koneksi Anda dan coba lagi.";
}
