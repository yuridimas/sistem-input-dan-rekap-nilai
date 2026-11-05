import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import api from "@/lib/api";
import { UsersPage } from "./UsersPage";

vi.mock("@/lib/api", () => ({ default: { get: vi.fn() } }));
const auth = vi.hoisted(() => ({ user: { id: "admin-1", role: "superadmin" as "superadmin" | "lecturer" } }));
vi.mock("@/features/auth/useAuth", () => ({
  useAuth: () => ({ ...auth, hasTokens: true, isLoading: false, error: null, retry: vi.fn() }),
}));

const users = [
  { id: "user-1", email: "ani@example.test", full_name: "Ani Putri", role: "lecturer", is_active: true, created_at: "2026-11-01T08:00:00Z", updated_at: "2026-11-01T08:00:00Z" },
  { id: "user-2", email: "admin@example.test", full_name: "Admin Seed", role: "superadmin", is_active: false, created_at: "2026-11-02T08:00:00Z", updated_at: "2026-11-02T08:00:00Z" },
];

function mount() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  const router = createMemoryRouter([
    { element: <ProtectedRoute allowedRoles={["superadmin"]} />, children: [{ path: "/users", element: <UsersPage /> }] },
    { path: "/dashboard", element: <p>Dashboard</p> },
  ], { initialEntries: ["/users"] });
  return render(<QueryClientProvider client={client}><RouterProvider router={router} /></QueryClientProvider>);
}

beforeEach(() => {
  vi.clearAllMocks();
  auth.user = { id: "admin-1", role: "superadmin" };
  vi.mocked(api.get).mockResolvedValue({ data: users });
});

describe("users page", () => {
  it("lists accounts, filters by role and active status, and searches name or email", async () => {
    mount();

    expect(await screen.findByText("Ani Putri")).toBeInTheDocument();
    expect(screen.getByText("ani@example.test")).toBeInTheDocument();
    expect(screen.getByRole("row", { name: /Ani Putri ani@example.test Dosen Aktif/ })).toBeInTheDocument();
    expect(screen.getByRole("row", { name: /Admin Seed admin@example.test Superadmin Nonaktif/ })).toBeInTheDocument();
    expect(screen.queryByText(/password/i)).not.toBeInTheDocument();

    await userEvent.selectOptions(screen.getByLabelText("Peran"), "lecturer");
    await userEvent.selectOptions(screen.getByLabelText("Status"), "true");
    await waitFor(() => expect(api.get).toHaveBeenLastCalledWith("/admin/users", {
      params: { role: "lecturer", is_active: true },
    }));

    await userEvent.type(screen.getByLabelText("Cari pengguna"), "ANI@");
    expect(screen.getByText("ani@example.test")).toBeInTheDocument();
    expect(screen.queryByText("admin@example.test")).not.toBeInTheDocument();
  });

  it("shows loading, an empty result, and a retryable API error", async () => {
    let resolveUsers: ((value: { data: typeof users }) => void) | undefined;
    vi.mocked(api.get).mockImplementationOnce(() => new Promise((resolve) => { resolveUsers = resolve; }));
    mount();
    expect(screen.getByRole("status")).toBeInTheDocument();
    resolveUsers?.({ data: [] });
    expect(await screen.findByText("Belum ada pengguna")).toBeInTheDocument();

    vi.mocked(api.get).mockRejectedValueOnce({ isAxiosError: true, response: { status: 500 } });
    await userEvent.click(screen.getByRole("button", { name: "Segarkan" }));
    expect(await screen.findByRole("button", { name: "Coba lagi" })).toBeInTheDocument();
    vi.mocked(api.get).mockResolvedValueOnce({ data: users });
    await userEvent.click(screen.getByRole("button", { name: "Coba lagi" }));
    expect(await screen.findByText("Ani Putri")).toBeInTheDocument();
  });

  it("redirects lecturers away from the superadmin-only route", async () => {
    auth.user = { id: "lecturer-1", role: "lecturer" };
    mount();
    expect(await screen.findByText("Dashboard")).toBeInTheDocument();
    expect(api.get).not.toHaveBeenCalled();
  });
});
