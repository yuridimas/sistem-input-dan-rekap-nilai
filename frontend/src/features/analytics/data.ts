import type { GradeComponent } from "@/features/academic/api";
import type { GradeGrid } from "@/features/grades/types";

export type AnalyticsMode = "finalized" | "draft";
export type ScoreCategory = GradeComponent["category"];

export interface DistributionBucket {
  label: string;
  count: number;
}

export interface BreakdownRow {
  studentId: string;
  nim: string;
  studentName: string;
  tugas: number | null;
  uts: number | null;
  uas: number | null;
  custom: number | null;
  finalScore: number;
}

export interface ClassAnalytics {
  distribution: DistributionBucket[];
  breakdown: BreakdownRow[];
  analyzedCount: number;
  excludedDraftCount: number;
  unavailableBreakdownCount: number;
}

export interface GradeHistoryEntry {
  grade_id?: string;
  enrollment_id: string;
  course: { id?: string; code?: string; name?: string; semester: string };
  class: { id?: string; section: string; academic_year: string };
  final_score: string;
  rank?: number | null;
  finalized_at?: string | null;
  components?: Array<{
    name: string;
    category: ScoreCategory;
    weight: string;
    max_score: string;
    score: string | null;
  }>;
}

export interface SemesterTrend {
  semester: string;
  average: number;
  count: number;
  entries: GradeHistoryEntry[];
}

export function distributionChartLabel(mode: AnalyticsMode) {
  return mode === "finalized"
    ? "Distribusi nilai final"
    : "Distribusi draft lengkap";
}

const BUCKETS = [
  { label: "0–<45", min: 0, max: 45 },
  { label: "45–<60", min: 45, max: 60 },
  { label: "60–<75", min: 60, max: 75 },
  { label: "75–<85", min: 75, max: 85 },
  { label: "85–100", min: 85, max: 101 },
] as const;

function numeric(value: string | number | null | undefined): number | null {
  if (value === undefined || value === null || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function scoreIsValid(score: number | null, component: GradeComponent) {
  const max = numeric(component.max_score);
  const weight = numeric(component.weight);
  return (
    score !== null &&
    max !== null &&
    max > 0 &&
    weight !== null &&
    weight > 0 &&
    score >= 0 &&
    score <= max
  );
}

function draftIsComplete(
  row: GradeGrid["grades"][number],
  components: GradeGrid["components"],
) {
  return (
    components.length > 0 &&
    components.every((component) =>
      scoreIsValid(numeric(row.scores[component.id]), component),
    )
  );
}

function breakdownFor(
  row: GradeGrid["grades"][number],
  components: GradeGrid["components"],
  finalScore: number,
): BreakdownRow {
  const values: Record<ScoreCategory, number> = {
    tugas: 0,
    uts: 0,
    uas: 0,
    custom: 0,
  };
  const complete = components.length > 0 && components.every((component) => {
    const score = numeric(row.scores[component.id]);
    if (!scoreIsValid(score, component)) return false;
    const max = Number(component.max_score);
    const weight = numeric(component.weight);
    if (weight === null || weight <= 0 || max <= 0) return false;
    values[component.category] += (score! / max) * weight;
    return true;
  });

  return {
    studentId: row.student.id,
    nim: row.student.nim,
    studentName: row.student.full_name,
    tugas: complete ? values.tugas : null,
    uts: complete ? values.uts : null,
    uas: complete ? values.uas : null,
    custom: complete ? values.custom : null,
    finalScore,
  };
}

export function buildClassAnalytics(
  grid: GradeGrid,
  mode: AnalyticsMode,
): ClassAnalytics {
  const selected: Array<{ row: GradeGrid["grades"][number]; finalScore: number }> = [];
  let excludedDraftCount = 0;

  for (const row of grid.grades) {
    if (mode === "finalized" && row.status !== "finalized") continue;
    if (mode === "draft" && row.status !== "draft") continue;
    const complete = draftIsComplete(row, grid.components);
    const finalScore = numeric(row.final_score);
    if (mode === "draft" && !complete) {
      excludedDraftCount += 1;
      continue;
    }
    if (finalScore === null || finalScore < 0 || finalScore > 100) {
      if (mode === "draft") excludedDraftCount += 1;
      continue;
    }
    selected.push({ row, finalScore });
  }

  const distribution = BUCKETS.map((bucket) => ({
    label: bucket.label,
    count: selected.filter(
      ({ finalScore }) => finalScore >= bucket.min && finalScore < bucket.max,
    ).length,
  }));
  const breakdown = selected
    .slice()
    .sort((left, right) =>
      left.row.student.nim.localeCompare(right.row.student.nim, undefined, {
        numeric: true,
      }),
    )
    .map(({ row, finalScore }) => breakdownFor(row, grid.components, finalScore));

  return {
    distribution,
    breakdown,
    analyzedCount: selected.length,
    excludedDraftCount,
    unavailableBreakdownCount: breakdown.filter((row) => row.tugas === null).length,
  };
}

export function buildStudentTrend(history: GradeHistoryEntry[]): SemesterTrend[] {
  const semesters = new Map<string, GradeHistoryEntry[]>();
  for (const entry of history) {
    const score = numeric(entry.final_score);
    if (score === null || score < 0 || score > 100) continue;
    const entries = semesters.get(entry.course.semester) ?? [];
    entries.push(entry);
    semesters.set(entry.course.semester, entries);
  }

  const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: "base" });
  return [...semesters.entries()]
    .sort(([left], [right]) => collator.compare(left, right))
    .map(([semester, entries]) => ({
      semester,
      average:
        entries.reduce((sum, entry) => sum + Number(entry.final_score), 0) /
        entries.length,
      count: entries.length,
      entries: entries.slice().sort((left, right) =>
        `${left.course.code ?? left.course.name ?? ""} ${left.class.section}`.localeCompare(
          `${right.course.code ?? right.course.name ?? ""} ${right.class.section}`,
          undefined,
          { numeric: true },
        ),
      ),
    }));
}
