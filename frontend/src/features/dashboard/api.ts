/**
 * Kontrak ringkasan server dan hook yang dipakai DashboardPage.
 * Cache dipisahkan per pengguna agar pergantian sesi tidak memakai ringkasan akun lain.
 */
import { useQuery } from "@tanstack/react-query";

import api from "@/lib/api";

/**
 * Ringkasan satu kelas; released_at null untuk kelas yang belum dirilis.
 */
export interface DashboardClass {
  id: string;
  section: string;
  academic_year: string;
  student_count: number;
  status: "pending" | "released";
  released_at: string | null;
  updated_at: string;
}

/**
 * Kelompok kelas dalam mata kuliah yang terlihat oleh pengguna.
 */
export interface DashboardCourse {
  id: string;
  code: string;
  name: string;
  semester: string;
  created_at: string;
  class_count: number;
  classes: DashboardClass[];
}

/**
 * Metadata mata kuliah tambahan untuk tautan daftar rilis terbaru.
 */
export interface DashboardRelease extends DashboardClass {
  course_id: string;
  course_code: string;
  course_name: string;
}

/**
 * Hitungan dan kelompok kelas siap tampil dari endpoint summary.
 */
export interface DashboardSummary {
  course_count: number;
  class_count: number;
  pending_class_count: number;
  courses: DashboardCourse[];
  recently_released: DashboardRelease[];
}

/**
 * Muat ringkasan hanya setelah userId tersedia; cache dianggap segar selama 30 detik.
 * @returns Hasil useQuery; satu retry otomatis untuk kegagalan sementara.
 */
export function useDashboard(userId: string | undefined) {
  return useQuery({
    queryKey: ["dashboard", "summary", userId],
    queryFn: async () => (await api.get<DashboardSummary>("/dashboard/summary")).data,
    enabled: Boolean(userId),
    staleTime: 30_000,
    retry: 1,
  });
}
