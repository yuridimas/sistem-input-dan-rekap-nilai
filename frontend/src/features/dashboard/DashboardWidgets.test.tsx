import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { RecentReleases } from "./RecentReleases";
import { SummaryCards } from "./SummaryCards";
import type { DashboardRelease, DashboardSummary } from "./api";

const data: DashboardSummary = {
  course_count: 8,
  class_count: 12,
  pending_class_count: 3,
  courses: [],
  recently_released: [],
};

describe("dashboard summary widgets", () => {
  it("labels summary counts according to the current role", () => {
    const { rerender } = render(<SummaryCards admin data={data} />);
    expect(screen.getByText("Seluruh mata kuliah")).toBeInTheDocument();

    rerender(<SummaryCards admin={false} data={data} />);
    expect(screen.getByText("Mata kuliah yang Anda ampu")).toBeInTheDocument();
  });

  it("opens the selected released class through its callback", async () => {
    const onSelect = vi.fn();
    const release: DashboardRelease = {
      id: "class-1",
      course_id: "course-1",
      course_code: "IF101",
      course_name: "Pemrograman",
      section: "A",
      academic_year: "2026/2027",
      student_count: 25,
      status: "released",
      released_at: "2026-10-25T08:00:00Z",
      updated_at: "2026-10-25T08:00:00Z",
    };
    render(<RecentReleases onSelect={onSelect} releases={[release]} />);

    await userEvent.click(screen.getByRole("button", { name: /Pemrograman/ }));

    expect(onSelect).toHaveBeenCalledWith("course-1", "class-1");
  });
});
