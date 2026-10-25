import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";

import api from "@/lib/api";
import { useAuth } from "@/features/auth/useAuth";

export interface Course {
  id: string;
  code: string;
  name: string;
  credits: number;
  semester: string;
  created_by: string;
}
export interface AcademicClass {
  id: string;
  course_id: string;
  section: string;
  academic_year: string;
  lecturer_id: string;
  has_finalized_grades: boolean;
}
export interface Student {
  id: string;
  nim: string;
  full_name: string;
  email: string | null;
}
export interface RosterEntry {
  id: string;
  student: Student;
}
export interface Lecturer {
  id: string;
  full_name: string;
  email: string;
  is_active: boolean;
}
export interface GradeComponent {
  id: string;
  name: string;
  category: "tugas" | "uts" | "uas" | "custom";
  weight: string;
  max_score: string;
  order_index: number;
}

export function useAcademicQuery<T>(path: string, enabled = true) {
  const { user } = useAuth();
  return useQuery({
    queryKey: ["academic", user?.id, path],
    queryFn: async () => (await api.get<T>(path)).data,
    enabled: Boolean(user) && enabled,
    retry: false,
  });
}

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
