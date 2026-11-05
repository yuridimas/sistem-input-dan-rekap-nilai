import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import api from "@/lib/api";
import { DashboardPage } from "./DashboardPage";

vi.mock("@/lib/api", () => ({ default: { get: vi.fn() } }));
const auth = vi.hoisted(() => ({ user: { id: "lecturer-1", role: "lecturer" as "superadmin" | "lecturer" } }));
vi.mock("@/features/auth/useAuth", () => ({ useAuth: () => ({ user: auth.user }) }));

const courses = Array.from({ length: 7 }, (_, index) => ({
  id: `course-${index}`,
  code: `C${index}`,
  name: `Mata Kuliah ${index}`,
  semester: "2026/1",
  created_at: new Date(Date.UTC(2026, 10, 7 - index)).toISOString(),
  classes: [],
}));

function mount() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  const router = createMemoryRouter([
    { path: "/dashboard", element: <DashboardPage /> },
    { path: "/courses", element: <p>Daftar mata kuliah</p> },
  ], { initialEntries: ["/dashboard"] });
  return render(<QueryClientProvider client={client}><RouterProvider router={router} /></QueryClientProvider>);
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.get).mockResolvedValue({ data: {
    course_count: courses.length,
    class_count: 0,
    pending_class_count: 0,
    courses,
    recently_released: [],
  } });
});

describe("dashboard course overview", () => {
  it("shows the five newest courses and links to the full course list", async () => {
    mount();

    expect(await screen.findByText("Mata Kuliah 0")).toBeInTheDocument();
    expect(screen.getByText("Mata Kuliah 4")).toBeInTheDocument();
    expect(screen.queryByText("Mata Kuliah 5")).not.toBeInTheDocument();
    expect(screen.getByText("7 mata kuliah")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("link", { name: "Lihat semua" }));
    expect(screen.getByText("Daftar mata kuliah")).toBeInTheDocument();
  });
});
