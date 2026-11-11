import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import api from "@/lib/api";
import { UsersPage } from "./UsersPage";

vi.mock("@/lib/api", () => ({ default: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() } }));
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
  vi.mocked(api.post).mockResolvedValue({ data: users[0] });
  vi.mocked(api.patch).mockResolvedValue({ data: users[0] });
  vi.mocked(api.delete).mockResolvedValue({ data: undefined });
});

describe("users page", () => {
  it("lists accounts, filters by role and active status, and searches name or email", async () => {
    mount();

    expect(await screen.findByText("Ani Putri")).toBeInTheDocument();
    expect(screen.getByText("ani@example.test")).toBeInTheDocument();
    expect(screen.getByRole("row", { name: /Ani Putri ani@example.test Dosen Aktif/ })).toBeInTheDocument();
    expect(screen.getByRole("row", { name: /Admin Seed admin@example.test Superadmin Nonaktif/ })).toBeInTheDocument();
    expect(screen.queryByText(/password/i)).not.toBeInTheDocument();
    const search = screen.getByRole("searchbox", { name: "Cari" });
    expect(search.parentElement).toHaveClass("flex", "items-center");
    expect(screen.getByText("ani@example.test").closest("span")).toHaveClass("whitespace-normal", "text-wrap");
    expect(screen.getByRole("button", { name: "Edit Ani Putri" })).toHaveClass("bg-blue-50");

    const roleFilter = screen.getByRole("combobox", { name: "Peran" });
    const activeFilter = screen.getByRole("combobox", { name: "Status" });
    await userEvent.selectOptions(roleFilter, "lecturer");
    await userEvent.selectOptions(activeFilter, "true");
    expect(api.get).toHaveBeenCalledTimes(1);
    await userEvent.click(screen.getByRole("button", { name: "Terapkan" }));
    await waitFor(() => expect(api.get).toHaveBeenLastCalledWith("/admin/users", {
      params: { role: "lecturer", is_active: true },
    }));

    await userEvent.click(screen.getByRole("button", { name: "Reset" }));
    await waitFor(() => expect(api.get).toHaveBeenLastCalledWith("/admin/users", { params: undefined }));

    await userEvent.type(screen.getByLabelText("Cari"), "ANI@");
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

  it("sorts users by name and paginates the resulting rows", async () => {
    const manyUsers = Array.from({ length: 12 }, (_, index) => ({
      ...users[0],
      id: `user-${index}`,
      email: `user-${index}@example.test`,
      full_name: `Akun ${String(12 - index).padStart(2, "0")}`,
    }));
    vi.mocked(api.get).mockResolvedValueOnce({ data: manyUsers });
    mount();

    await userEvent.click(await screen.findByRole("button", { name: "Nama" }));
    expect(screen.getByRole("row", { name: /Akun 01/ })).toBeInTheDocument();
    expect(screen.queryByRole("row", { name: /Akun 12/ })).not.toBeInTheDocument();
    expect(screen.getByText("1–10 dari 12 baris")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Halaman berikutnya" }));
    expect(screen.getByRole("row", { name: /Akun 11/ })).toBeInTheDocument();
    expect(screen.queryByRole("row", { name: /Akun 01/ })).not.toBeInTheDocument();
  });

  it("creates an account from the header action", async () => {
    mount();

    await userEvent.click(await screen.findByRole("button", { name: "Tambah pengguna" }));
    await userEvent.type(screen.getByLabelText("Nama lengkap"), "Dewi Lestari");
    await userEvent.type(screen.getByLabelText("Email akun"), "dewi@example.test");
    await userEvent.type(screen.getByLabelText("Kata sandi"), "secret123");
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Peran" }), "lecturer");
    await userEvent.click(screen.getByRole("button", { name: "Simpan pengguna" }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith("/admin/users", {
      email: "dewi@example.test",
      full_name: "Dewi Lestari",
      password: "secret123",
      role: "lecturer",
    }));
  });

  it("redirects lecturers away from the superadmin-only route", async () => {
    auth.user = { id: "lecturer-1", role: "lecturer" };
    mount();
    expect(await screen.findByText("Dashboard")).toBeInTheDocument();
    expect(api.get).not.toHaveBeenCalled();
  });
});
