/**
 * Kontrak JSON penilaian yang dipakai engine draft, hook, dan analytics.
 * Angka Decimal dari API dipertahankan sebagai string sampai diperlukan untuk tampilan/validasi.
 */
import type { GradeComponent, Student } from "@/features/academic/api";

/**
 * Satu enrollment dalam grid; total null berarti total draft belum tersedia.
 */
export interface GradeRow {
  enrollment_id: string;
  student: Student;
  scores: Record<string, string>;
  final_score: string | null;
  status: "draft" | "finalized";
}
/**
 * Konfigurasi komponen dan roster sebagai satu snapshot kelas.
 */
export interface GradeGrid {
  class_id: string;
  components: GradeComponent[];
  grades: GradeRow[];
}
/**
 * Acknowledgement PUT yang dipakai engine untuk memperbarui total/status baris.
 */
export interface SavedGrade {
  enrollment_id: string;
  final_score: string;
  status: "draft" | "finalized";
}
/**
 * Patch skor: string menyimpan angka, null menghapus, key absen tidak mengubah.
 */
export type ScoreChanges = Record<string, string | null>;
/**
 * Identitas tampilan sel yang belum terisi menurut validasi finalisasi server.
 */
export interface MissingScore {
  student_nim: string;
  component_name: string;
}
/**
 * Jumlah nilai final dan task diterima antrean; notified bukan email yang sudah sampai.
 */
export interface FinalizeResult {
  finalized_count: number;
  notified: number;
}
