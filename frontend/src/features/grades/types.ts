import type { GradeComponent, Student } from "@/features/academic/api";

export interface GradeRow {
  enrollment_id: string;
  student: Student;
  scores: Record<string, string>;
  final_score: string | null;
  status: "draft" | "finalized";
}
export interface GradeGrid {
  class_id: string;
  components: GradeComponent[];
  grades: GradeRow[];
}
export interface SavedGrade {
  enrollment_id: string;
  final_score: string;
  status: "draft" | "finalized";
}
export type ScoreChanges = Record<string, string | null>;
export interface MissingScore {
  student_nim: string;
  component_name: string;
}
export interface FinalizeResult {
  finalized_count: number;
  notified: number;
}
