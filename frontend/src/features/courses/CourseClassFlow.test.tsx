import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createMemoryRouter, RouterProvider, useParams } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { Layout } from "@/components/Layout";
import { ClassDetailPage } from "@/features/classes/ClassDetailPage";
import api from "@/lib/api";
import { CoursesPage } from "./CoursesPage";
import { CourseDetailPage } from "./CourseDetailPage";

vi.mock("@/lib/api", () => ({ default: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() } }));
const state = vi.hoisted(() => ({
  user: { id: "lecturer", role: "lecturer" as "lecturer" | "superadmin", email: "lecturer@example.test", full_name: "Dosen", is_active: true },
  locked: false,
}));
vi.mock("@/features/auth/useAuth", () => ({ useAuth: () => ({ user: state.user, hasTokens: true }) }));
const course = { id: "c1", code: "IF101", name: "Pemrograman", credits: 3, semester: "2026/1", created_by: "another" };
const class_ = { id: "k1", course_id: "c1", section: "A", academic_year: "2026/2027", lecturer_id: "lecturer", has_finalized_grades: false };
const roster = [{ id: "enrollment-1", student: { id: "student-1", nim: "001", full_name: "Budi", email: null } }];
function StudentTarget() { return <p>Detail mahasiswa {useParams().studentId}</p>; }
function mount(entry = "/courses") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  const router = createMemoryRouter([{ element: <Layout />, children: [
    { path: "/courses", element: <CoursesPage /> },
    { path: "/courses/:courseId", element: <CourseDetailPage /> },
    { path: "/classes/:classId", element: <ClassDetailPage /> },
    { path: "/students/:studentId", element: <StudentTarget /> },
  ] }], { initialEntries: [entry] });
  render(<QueryClientProvider client={client}><RouterProvider router={router} /></QueryClientProvider>);
  return router;
}
beforeEach(() => {
  vi.clearAllMocks();
  state.user.role = "lecturer";
  state.locked = false;
  vi.mocked(api.get).mockImplementation(async (path) => {
    if (path === "/courses") return { data: [course] };
    if (path === "/courses/c1") return { data: course };
    if (path === "/classes") return { data: [{ ...class_, has_finalized_grades: state.locked }, { ...class_, id: "other", course_id: "c2", section: "B" }] };
    if (path === "/classes/k1") return { data: { ...class_, has_finalized_grades: state.locked } };
    if (path === "/classes/k1/roster") return { data: roster };
    throw new Error("Unexpected fixture route: " + path);
  });
});

describe("course class roster navigation", () => {
  it.each([
    { role: "lecturer" as const, locked: false },
    { role: "lecturer" as const, locked: true },
    { role: "superadmin" as const, locked: false },
    { role: "superadmin" as const, locked: true },
  ])("keeps route IDs and menu context for $role, locked=$locked", async ({ role, locked }) => {
    state.user.role = role;
    state.locked = locked;
    const router = mount();
    const label = role === "superadmin" ? "Semua Mata Kuliah" : "Mata Kuliah Saya";
    const menu = () => within(screen.getByRole("navigation", { name: "Navigasi utama" }));
    expect(menu().getByRole("link", { name: label })).toHaveAttribute("aria-current", "page");
    await userEvent.click(await screen.findByRole("link", { name: "Lihat mata kuliah Pemrograman" }));
    expect(router.state.location.pathname).toBe("/courses/c1");
    const courseCrumb = screen.getByRole("navigation", { name: "Breadcrumb" });
    expect(within(courseCrumb).getByRole("link", { name: label })).toHaveAttribute("href", "/courses");
    expect(courseCrumb.querySelector('[aria-current="page"]')).toHaveTextContent(course.name);
    expect(screen.queryByRole("link", { name: "Lihat kelas B (2026/2027)" })).not.toBeInTheDocument();
    await userEvent.click(await screen.findByRole("link", { name: "Lihat kelas A (2026/2027)" }));
    expect(router.state.location.pathname).toBe("/classes/k1");
    await screen.findByText("Budi");
    const classCrumb = screen.getByRole("navigation", { name: "Breadcrumb" });
    expect(within(classCrumb).getByRole("link", { name: course.name })).toHaveAttribute("href", "/courses/c1");
    expect(classCrumb.querySelector('[aria-current="page"]')).toHaveTextContent("Kelas A (2026/2027)");
    expect(menu().getByRole("link", { name: label })).toHaveAttribute("aria-current", "page");
    if (locked) {
      expect(screen.getByRole("button", { name: "Tambah mahasiswa ke kelas" })).toBeDisabled();
      expect(screen.queryByRole("button", { name: "Keluarkan Budi" })).not.toBeInTheDocument();
    }
    const studentLink = screen.getByRole("link", { name: "Lihat mahasiswa Budi (001)" });
    studentLink.focus();
    await userEvent.keyboard("{Enter}");
    expect(await screen.findByText("Detail mahasiswa student-1")).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/students/student-1");
    expect(menu().getByRole("link", { name: "Mahasiswa" })).toHaveAttribute("aria-current", "page");
  });

  it("loads class context directly without visiting the course index", async () => {
    mount("/classes/k1");
    expect(await screen.findByRole("link", { name: "Lihat mahasiswa Budi (001)" })).toBeInTheDocument();
    expect(within(screen.getByRole("navigation", { name: "Breadcrumb" })).getByRole("link", { name: "Pemrograman" })).toHaveAttribute("href", "/courses/c1");
    expect(api.get).toHaveBeenCalledWith("/classes/k1");
    expect(api.get).toHaveBeenCalledWith("/courses/c1");
  });

  it.each(["pending", "error"])("keeps sidebar active while class metadata is %s", async (status) => {
    if (status === "pending") vi.mocked(api.get).mockImplementation(() => new Promise(() => {}));
    else vi.mocked(api.get).mockRejectedValue(new Error("offline"));
    mount("/classes/k1?tab=grades");
    if (status === "error") await screen.findByRole("alert");
    const menu = within(screen.getByRole("navigation", { name: "Navigasi utama" }));
    expect(menu.getByRole("link", { name: "Mata Kuliah Saya" })).toHaveAttribute("aria-current", "page");
    expect(screen.queryByRole("navigation", { name: "Breadcrumb" })).not.toBeInTheDocument();
  });
});
