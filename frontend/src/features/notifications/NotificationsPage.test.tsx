/**
 * Integration test audit/retry notifikasi dan pembatasan role dengan API palsu.
 * Status antrean diperiksa terpisah dari sukses kirim agar UI tidak memberi konfirmasi palsu.
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import api from "@/lib/api";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { NotificationsPage } from "./NotificationsPage";

vi.mock("@/lib/api", () => ({ default: { get: vi.fn(), post: vi.fn() } }));
const auth = vi.hoisted(() => ({ user: { id: "admin-1", role: "superadmin" as "superadmin" | "lecturer" } }));
vi.mock("@/features/auth/useAuth", () => ({
  useAuth: () => ({ ...auth, hasTokens: true, isLoading: false, error: null, retry: vi.fn() }),
}));

const notifications = [
  { id: "failed-1", grade_id: "grade-1", student_email: "mahasiswa@example.com", status: "failed", error_message: "SMTP tidak tersedia", sent_at: null, created_at: "2026-10-26T08:00:00Z" },
  { id: "sent-1", grade_id: "grade-2", student_email: "lain@example.com", status: "sent", error_message: null, sent_at: "2026-10-26T08:00:00Z", created_at: "2026-10-26T07:00:00Z" },
];
const queuedNotification = { ...notifications[0], status: "queued" as const, error_message: null };

/**
 * Simulasikan filter status server agar request dan pergantian isi tabel dapat diperiksa.
 */
function mockNotificationList() {
  vi.mocked(api.get).mockImplementation(async (_path, config) => {
    const status = (config?.params as { status?: string } | undefined)?.status;
    const data = status === "failed"
      ? [notifications[0]]
      : status === "sent"
        ? [notifications[1]]
        : status === "queued"
          ? [queuedNotification]
          : notifications;
    return { data };
  });
}

/**
 * Pasang guard superadmin pada memory router dengan cache baru untuk tiap skenario.
 */
function mount() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  const router = createMemoryRouter([
    { element: <ProtectedRoute allowedRoles={["superadmin"]} />, children: [{ path: "/notifications", element: <NotificationsPage /> }] },
    { path: "/dashboard", element: <p>Dashboard</p> },
  ], { initialEntries: ["/notifications"] });
  return render(<QueryClientProvider client={client}><RouterProvider router={router} /></QueryClientProvider>);
}

beforeEach(() => {
  vi.clearAllMocks();
  auth.user = { id: "admin-1", role: "superadmin" };
});

describe("notifications page", () => {
  it("filters statuses and retries a failed notification", async () => {
    mockNotificationList();
    vi.mocked(api.post).mockResolvedValue({ data: queuedNotification });
    mount();

    expect(await screen.findByText("SMTP tidak tersedia")).toBeInTheDocument();
    expect(api.get).toHaveBeenCalledWith("/admin/notifications", { params: { status: "failed" } });
    expect(screen.getByRole("columnheader", { name: "Dibuat" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Terkirim" })).toBeInTheDocument();
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Status" }), "sent");
    expect(screen.getByText("lain@example.com")).toBeInTheDocument();
    expect(screen.queryByText("mahasiswa@example.com")).not.toBeInTheDocument();
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Status" }), "all");
    await userEvent.click(screen.getByRole("button", { name: "Kirim ulang ke mahasiswa@example.com" }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith("/admin/notifications/failed-1/retry"));
    await waitFor(() => {
      const email = screen.getByText("mahasiswa@example.com");
      expect(email.closest("tr")).toHaveTextContent("Antrean");
    });
    expect(screen.getByRole("combobox", { name: "Status" })).toHaveValue("queued");
  });

  it("sorts the notification list by student email", async () => {
    mockNotificationList();
    mount();
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Status" }), "all");

    await userEvent.click(await screen.findByRole("button", { name: "Email mahasiswa" }));
    const rows = screen.getAllByRole("row").slice(1);
    expect(rows[0]).toHaveTextContent("lain@example.com");
    expect(rows[1]).toHaveTextContent("mahasiswa@example.com");
  });

  it("redirects lecturers away from the superadmin-only route", async () => {
    auth.user = { id: "lecturer-1", role: "lecturer" };
    mount();
    expect(await screen.findByText("Dashboard")).toBeInTheDocument();
    expect(api.get).not.toHaveBeenCalled();
  });

  it("offers retry again after the request fails", async () => {
    mockNotificationList();
    vi.mocked(api.post).mockRejectedValue(new Error("offline"));
    mount();
    await userEvent.click(await screen.findByRole("button", { name: "Kirim ulang ke mahasiswa@example.com" }));
    expect(await screen.findByText(/Gagal mengirim ulang/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Kirim ulang ke mahasiswa@example.com" })).toBeEnabled();
  });
});
