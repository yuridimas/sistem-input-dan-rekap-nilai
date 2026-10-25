import { describe, expect, it } from "vitest";

import type { GradeGrid } from "@/features/grades/types";
import {
  buildClassAnalytics,
  buildStudentTrend,
  distributionChartLabel,
  type GradeHistoryEntry,
} from "./data";

const components: GradeGrid["components"] = [
  { id: "a1", name: "Tugas 1", category: "tugas", weight: "20", max_score: "50", order_index: 0 },
  { id: "a2", name: "Tugas 2", category: "tugas", weight: "10", max_score: "100", order_index: 1 },
  { id: "mid", name: "UTS", category: "uts", weight: "30", max_score: "100", order_index: 2 },
  { id: "final", name: "UAS", category: "uas", weight: "40", max_score: "80", order_index: 3 },
];

function grid(overrides: Partial<GradeGrid["grades"][number]>[] = []): GradeGrid {
  return {
    class_id: "class-1",
    components,
    grades: overrides.map((override, index) => ({
      enrollment_id: `e${index}`,
      student: { id: `s${index}`, nim: `${index + 1}`, full_name: `Mahasiswa ${index + 1}`, email: null },
      scores: { a1: "25", a2: "100", mid: "75", final: "60" },
      final_score: "75",
      status: "finalized",
      ...override,
    })),
  };
}

describe("class analytics transformations", () => {
  it("uses a concise accessible label for the selected class distribution", () => {
    expect(distributionChartLabel("finalized")).toBe("Distribusi nilai final");
  });

  it("places boundary scores into non-overlapping distribution buckets", () => {
    const result = buildClassAnalytics(
      grid([45, 60, 75, 85, 100].map((score) => ({ final_score: String(score) }))),
      "finalized",
    );

    expect(result.distribution.map((bucket) => bucket.count)).toEqual([0, 1, 1, 1, 2]);
    expect(result.analyzedCount).toBe(5);
  });

  it("includes only complete drafts and counts omitted incomplete drafts", () => {
    const result = buildClassAnalytics(
      grid([
        { status: "draft", final_score: "0", scores: { a1: "0", a2: "0", mid: "0", final: "0" } },
        { status: "draft", final_score: "50", scores: { a1: "25", mid: "50" } },
        { status: "finalized", final_score: "90" },
      ]),
      "draft",
    );

    expect(result.analyzedCount).toBe(1);
    expect(result.excludedDraftCount).toBe(1);
    expect(result.distribution.reduce((sum, bucket) => sum + bucket.count, 0)).toBe(1);
    expect(result.breakdown[0]).toMatchObject({ tugas: 0, uts: 0, uas: 0, custom: 0 });
  });

  it("normalizes each score by max score and aggregates category weights without rounding", () => {
    const result = buildClassAnalytics(grid([{}]), "finalized");

    expect(result.breakdown[0]).toMatchObject({
      tugas: 20,
      uts: 22.5,
      uas: 30,
      custom: 0,
      finalScore: 75,
    });
  });

  it("leaves legacy finalized breakdown unavailable when any component is missing", () => {
    const result = buildClassAnalytics(
      grid([{ status: "finalized", scores: { a1: "25", mid: "75", final: "60" } }]),
      "finalized",
    );

    expect(result.analyzedCount).toBe(1);
    expect(result.breakdown[0].tugas).toBeNull();
    expect(result.breakdown[0].finalScore).toBe(75);
  });

  it("retains fractional contributions until the chart formats them", () => {
    const fractional: GradeGrid = {
      class_id: "fractional",
      components: [
        { id: "small", name: "Tugas", category: "tugas", weight: "0.1", max_score: "3", order_index: 0 },
        { id: "rest", name: "UTS", category: "uts", weight: "99.9", max_score: "100", order_index: 1 },
      ],
      grades: [{
        enrollment_id: "fractional-row",
        student: { id: "fractional-student", nim: "10", full_name: "Desimal", email: null },
        scores: { small: "1", rest: "50" },
        final_score: "49.95",
        status: "finalized",
      }],
    };
    const result = buildClassAnalytics(fractional, "finalized");

    expect(result.breakdown[0].tugas).toBeCloseTo(0.1 / 3);
    expect(result.breakdown[0].uts).toBe(49.95);
  });
});

describe("student history trend", () => {
  it("sorts semester labels naturally and averages accessible finalized class results", () => {
    const history: GradeHistoryEntry[] = [
      { enrollment_id: "e10", course: { semester: "Semester 10" }, final_score: "80", class: { section: "B", academic_year: "2025/2026" } },
      { enrollment_id: "e2a", course: { semester: "Semester 2" }, final_score: "60", class: { section: "A", academic_year: "2024/2025" } },
      { enrollment_id: "e2b", course: { semester: "Semester 2" }, final_score: "80", class: { section: "C", academic_year: "2024/2025" } },
    ];

    expect(buildStudentTrend(history)).toEqual([
      expect.objectContaining({ semester: "Semester 2", average: 70, count: 2 }),
      expect.objectContaining({ semester: "Semester 10", average: 80, count: 1 }),
    ]);
  });

  it("does not invent a zero result for an empty semester", () => {
    expect(buildStudentTrend([])).toEqual([]);
  });
});
