import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import type { AcademicClass } from "@/features/academic/api";
import { CourseClassesTable } from "./CourseClassesTable";

const rows: AcademicClass[] = [
  { id: "k1", course_id: "c1", section: "A", academic_year: "2026/2027", lecturer_id: "owner", has_finalized_grades: true },
  { id: "k2", course_id: "c1", section: "A", academic_year: "2025/2026", lecturer_id: "owner", has_finalized_grades: false },
];

function mount(data = rows, overrides = {}) {
  const props = { rows: data, isPending: false, isFetching: false, error: null, onRefresh: vi.fn(), onEdit: vi.fn(), onDelete: vi.fn(), ...overrides };
  render(<MemoryRouter><CourseClassesTable {...props} /></MemoryRouter>);
  return props;
}

describe("course classes table", () => {
  it("disambiguates sections by year and keeps locked classes readable and editable", async () => {
    const props = mount();
    expect(screen.getByRole("link", { name: "Lihat kelas A (2026/2027)" })).toHaveAttribute("href", "/classes/k1");
    expect(screen.getByRole("link", { name: "Lihat kelas A (2025/2026)" })).toHaveAttribute("href", "/classes/k2");
    expect(screen.getByText("Roster terkunci")).toBeInTheDocument();
    expect(screen.getByText("Roster terbuka")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Edit kelas A (2026/2027)" }));
    expect(props.onEdit).toHaveBeenCalledWith(rows[0]);
    await userEvent.click(screen.getByRole("button", { name: "Hapus kelas A (2025/2026)" }));
    expect(props.onDelete).toHaveBeenCalledWith(rows[1]);
  });

  it("searches locally by section and year and retains search on refresh", async () => {
    const props = mount();
    const search = screen.getByRole("searchbox", { name: "Cari" });
    await userEvent.type(search, "2025");
    expect(screen.queryByRole("link", { name: "Lihat kelas A (2026/2027)" })).not.toBeInTheDocument();
    expect(props.onRefresh).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole("button", { name: "Segarkan" }));
    expect(props.onRefresh).toHaveBeenCalledOnce();
    expect(search).toHaveValue("2025");
    await userEvent.clear(search);
    await userEvent.type(search, "tidak cocok");
    expect(screen.getByRole("status")).toHaveTextContent("Tidak ada kelas yang cocok dengan pencarian.");
  });

  it("sorts and paginates then resets to a valid page after searching", async () => {
    mount(Array.from({ length: 13 }, (_, i) => ({ ...rows[0], id: `k${i}`, section: String(12 - i).padStart(2, "0") })));
    await userEvent.click(screen.getByRole("button", { name: "Kelas" }));
    expect(screen.getAllByRole("row")[1]).toHaveTextContent("Kelas 00");
    await userEvent.click(screen.getByRole("button", { name: "Halaman berikutnya" }));
    expect(screen.getByRole("link", { name: "Lihat kelas 12 (2026/2027)" })).toBeInTheDocument();
    await userEvent.type(screen.getByRole("searchbox", { name: "Cari" }), "00");
    await waitFor(() => expect(screen.getByRole("link", { name: "Lihat kelas 00 (2026/2027)" })).toBeInTheDocument());
    expect(screen.getByRole("button", { name: "Halaman sebelumnya" })).toBeDisabled();
  });

  it.each(["empty", "pending", "error"])("keeps controls for %s data", (state) => {
    mount([], { isPending: state === "pending", error: state === "error" ? new Error("offline") : null });
    expect(screen.getByRole("searchbox", { name: "Cari" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Segarkan" })).toBeInTheDocument();
    if (state === "error") expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});
