/**
 * Warna/label kategori bersama untuk chart dan legenda.
 * Menggunakan tipe kategori dari data analytics agar tampilan tidak memiliki kategori terpisah.
 */
import type { ScoreCategory } from "./data";

export const CATEGORY_COLORS: Record<ScoreCategory, string> = {
  tugas: "#2563eb",
  uts: "#d97706",
  uas: "#059669",
  custom: "#7c3aed",
};

export const CATEGORY_LABELS: Record<ScoreCategory, string> = {
  tugas: "Tugas",
  uts: "UTS",
  uas: "UAS",
  custom: "Kustom",
};
