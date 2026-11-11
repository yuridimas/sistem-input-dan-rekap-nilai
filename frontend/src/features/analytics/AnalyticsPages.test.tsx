/**
 * Integration test halaman analytics dengan API palsu dan router/cache terisolasi.
 * Fokus pada pemilihan populasi, state query, dan akses data/tabel tanpa backend nyata.
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import api from "@/lib/api";
import type { GradeGrid } from "@/features/grades/types";
import { ClassDetailPage } from "@/features/classes/ClassDetailPage";
import { ClassAnalyticsPanel } from "./ClassAnalyticsPanel";
import { StudentDetailPage } from "./StudentDetailPage";
import { BreakdownLegend } from "./Charts";

vi.mock("@/lib/api", () => ({ default: { get: vi.fn() } }));
vi.mock("@/features/auth/useAuth", () => ({
  useAuth: () => ({ user: { id: "lecturer-1", role: "lecturer" }, hasTokens: true }),
}));

const grid: GradeGrid = {
  class_id: "class-1",
  components: [
    { id: "uts", name: "UTS", category: "uts", weight: "50", max_score: "100", order_index: 0 },
    { id: "uas", name: "UAS", category: "uas", weight: "50", max_score: "100", order_index: 1 },
  ],
  grades: [
    { enrollment_id: "e1", student: { id: "s1", nim: "001", full_name: "Satu", email: null }, scores: { uts: "80", uas: "70" }, final_score: "75", status: "finalized" },
    { enrollment_id: "e2", student: { id: "s2", nim: "002", full_name: "Dua", email: null }, scores: { uts: "60" }, final_score: "30", status: "draft" },
  ],
};

/**
 * Pasang halaman pada memory router dan QueryClient baru agar cache tidak bocor antar-test.
 */
function mount(element: React.ReactNode, route = "/") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  const router = createMemoryRouter([
    { path: "/", element },
    { path: "/classes/:classId", element },
    { path: "/students/:studentId", element },
  ], { initialEntries: [route] });
  return render(<QueryClientProvider client={client}><RouterProvider router={router} /></QueryClientProvider>);
}

beforeEach(() => vi.clearAllMocks());

describe("class analytics panel", () => {
  it("keeps every component label visible in a wrapping chart legend", () => {
    render(<BreakdownLegend />);
    expect(screen.getByRole("list", { name: "Kategori kontribusi" })).toHaveTextContent(/Tugas\s*UTS\s*UAS\s*Kustom/);
  });

  it("filters final and complete draft results without mixing statuses", async () => {
    vi.mocked(api.get).mockResolvedValue({ data: grid });
    mount(<ClassAnalyticsPanel classId="class-1" />, "/");
    await screen.findByText(/Menganalisis 1 mahasiswa dengan nilai final/);
    expect(screen.queryByText("1 draft belum lengkap atau tidak valid dikecualikan.")).not.toBeInTheDocument();
    await userEvent.selectOptions(screen.getByLabelText("Data grafik"), "draft");
    expect(await screen.findByText(/Belum ada draft lengkap.*1 draft/)).toBeInTheDocument();
  });

  it("shows the saved-data caveat while local grade edits exist", async () => {
    vi.mocked(api.get).mockResolvedValue({ data: grid });
    mount(<ClassAnalyticsPanel classId="class-1" hasUnsavedChanges />);
    expect(await screen.findByText(/Grafik memakai data tersimpan/)).toBeInTheDocument();
  });

  it("offers a retry after the saved grades query fails", async () => {
    vi.mocked(api.get)
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce({ data: grid });
    mount(<ClassAnalyticsPanel classId="class-1" />);
    await userEvent.click(await screen.findByRole("button", { name: "Coba lagi" }));
    expect(await screen.findByText(/Menganalisis 1 mahasiswa dengan nilai final/)).toBeInTheDocument();
    expect(api.get).toHaveBeenCalledTimes(2);
  });

  it("keeps local grade edits and the navigation guard while switching to analytics", async () => {
    const editable: GradeGrid = {
      ...grid,
      grades: grid.grades.map((row) => ({ ...row, status: "draft" as const })),
    };
    vi.mocked(api.get).mockImplementation(async (path) => {
      if (path === "/classes/class-1") return { data: { id: "class-1", course_id: "course-1", section: "A", academic_year: "2026/2027", lecturer_id: "lecturer-1", has_finalized_grades: false } };
      if (path === "/courses/course-1") return { data: { id: "course-1", code: "IF101", name: "Pemrograman", credits: 3, semester: "Semester 1", created_by: "lecturer-1" } };
      return { data: editable };
    });
    const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
    const router = createMemoryRouter([
      { path: "/classes/:classId", element: <ClassDetailPage /> },
      { path: "/courses", element: <p>Daftar mata kuliah</p> },
    ], { initialEntries: ["/classes/class-1?tab=grades"] });
    render(<QueryClientProvider client={client}><RouterProvider router={router} /></QueryClientProvider>);

    const input = await screen.findByLabelText("001 Satu — UTS");
    fireEvent.change(input, { target: { value: "101" } });
    await userEvent.click(screen.getByRole("tab", { name: "Analisis" }));
    expect(await screen.findByText(/Grafik memakai data tersimpan/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("tab", { name: "Nilai" }));
    expect(await screen.findByLabelText("001 Satu — UTS")).toHaveValue("101");

    await userEvent.click(screen.getByRole("link", { name: "Mata Kuliah Saya" }));
    expect(await screen.findByRole("dialog")).toHaveTextContent("Perubahan nilai belum selesai");
    expect(screen.queryByText("Daftar mata kuliah")).not.toBeInTheDocument();
  });

  it("shows class PDF and Excel exports when finalized grades exist", async () => {
    vi.mocked(api.get).mockImplementation(async (path) => {
      if (path === "/classes/class-1") return { data: { id: "class-1", course_id: "course-1", section: "A", academic_year: "2026/2027", lecturer_id: "lecturer-1", has_finalized_grades: true } };
      if (path === "/courses/course-1") return { data: { id: "course-1", code: "IF101", name: "Pemrograman", credits: 3, semester: "Semester 1", created_by: "lecturer-1" } };
      return { data: [] };
    });
    mount(<ClassDetailPage />, "/classes/class-1");
    expect(await screen.findByRole("button", { name: "Unduh PDF" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Unduh Excel" })).toBeInTheDocument();
  });
});

describe("student detail page", () => {
  it("shows identity and a clear empty-history state", async () => {
    vi.mocked(api.get).mockImplementation(async (path) => ({
      data: path.endsWith("/history") ? [] : { id: "s1", nim: "001", full_name: "Satu", email: null },
    }));
    mount(<StudentDetailPage />, "/students/s1");
    expect(await screen.findByRole("heading", { name: "Satu" })).toBeInTheDocument();
    expect(screen.getByText(/NIM 001/)).toBeInTheDocument();
    expect(await screen.findByText("Belum ada riwayat nilai final untuk ditampilkan.")).toBeInTheDocument();
    await waitFor(() => expect(api.get).toHaveBeenCalledWith("/students/s1/history"));
  });

  it("shows one finalized semester as a real single-point trend", async () => {
    vi.mocked(api.get).mockImplementation(async (path) => ({
      data: path.endsWith("/history")
        ? [{
            grade_id: "g1",
            enrollment_id: "enrollment-1",
            course: { code: "IF1", semester: "Semester 1" },
            class: { section: "A", academic_year: "2026/2027" },
            final_score: "42.5",
          }]
        : { id: "s1", nim: "001", full_name: "Satu", email: null },
    }));
    mount(<StudentDetailPage />, "/students/s1");
    expect(await screen.findByRole("heading", { name: "Rata-rata nilai per semester", level: 2 })).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Riwayat nilai final" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Unduh PDF nilai IF1, kelas A 2026\/2027/ })).toBeInTheDocument();
    await userEvent.click(await screen.findByText("Lihat tabel data"));
    const table = screen.getByRole("region", { name: "Tabel rata-rata nilai per semester" });
    expect(table).toHaveTextContent("42.50");
    expect(table).toHaveTextContent("1");
  });
});
