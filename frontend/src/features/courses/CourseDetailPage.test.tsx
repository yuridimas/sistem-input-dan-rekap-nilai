import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import api from "@/lib/api";
import { CourseDetailPage } from "./CourseDetailPage";

vi.mock("@/lib/api", () => ({ default: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() } }));
vi.mock("@/features/auth/useAuth", () => ({ useAuth: () => ({ user: { id: "lecturer", role: "lecturer" } }) }));
const course = { id: "c1", code: "IF101", name: "Pemrograman", credits: 3, semester: "2026/1", created_by: "another" };
const classes = [
  { id: "k1", course_id: "c1", section: "A", academic_year: "2026/2027", lecturer_id: "lecturer", has_finalized_grades: false },
  { id: "k2", course_id: "c2", section: "B", academic_year: "2026/2027", lecturer_id: "lecturer", has_finalized_grades: false },
];
function mount() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  const router = createMemoryRouter([{ path: "/courses/:courseId", element: <CourseDetailPage /> }], { initialEntries: ["/courses/c1"] });
  render(<QueryClientProvider client={client}><RouterProvider router={router} /></QueryClientProvider>);
}
beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.get).mockImplementation(async (path) => ({ data: path === "/courses/c1" ? course : classes }));
});

describe("course detail class index", () => {
  it("scopes classes to this course while allowing assigned lecturer class actions", async () => {
    mount();
    expect(await screen.findByRole("link", { name: "Lihat kelas A (2026/2027)" })).toHaveAttribute("href", "/classes/k1");
    expect(screen.queryByRole("link", { name: "Lihat kelas B (2026/2027)" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Edit mata kuliah" })).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Edit kelas A (2026/2027)" }));
    const dialog = await screen.findByRole("dialog", { name: "Edit kelas" });
    expect(within(dialog).getByLabelText("Seksi kelas")).toHaveValue("A");
    await userEvent.click(within(dialog).getByRole("button", { name: "Batal" }));
    await userEvent.click(screen.getByRole("button", { name: "Hapus kelas A (2026/2027)" }));
    expect(await screen.findByRole("dialog", { name: "Hapus kelas A" })).toBeInTheDocument();
  });

  it("opens the existing create-class dialog", async () => {
    mount();
    await userEvent.click(await screen.findByRole("button", { name: "Tambah kelas" }));
    expect(await screen.findByRole("dialog", { name: "Tambah kelas" })).toBeInTheDocument();
  });
});
