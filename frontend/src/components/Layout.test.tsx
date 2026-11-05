import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { Layout } from "./Layout";

const state = vi.hoisted(() => ({
  user: { id: "admin-1", email: "admin@example.test", full_name: "Admin User", role: "superadmin" as "superadmin" | "lecturer", is_active: true },
  clear: vi.fn(),
}));

vi.mock("@/features/auth/useAuth", () => ({ useAuth: () => ({ user: state.user }) }));
vi.mock("@/stores/authStore", () => ({
  useAuthStore: (selector: (value: { clear: () => void }) => unknown) => selector({ clear: state.clear }),
}));

function mount() {
  const client = new QueryClient();
  const router = createMemoryRouter([
    { element: <Layout />, children: [
      { path: "/dashboard", element: <p>Dashboard content</p> },
      { path: "/notifications", element: <p>Notifications content</p> },
    ] },
    { path: "/login", element: <p>Login page</p> },
  ], { initialEntries: ["/dashboard"] });
  render(<QueryClientProvider client={client}><RouterProvider router={router} /></QueryClientProvider>);
}

beforeEach(() => {
  state.user = { id: "admin-1", email: "admin@example.test", full_name: "Admin User", role: "superadmin", is_active: true };
  state.clear.mockClear();
});

describe("authenticated layout profile and notifications", () => {
  it("keeps profile and logout in the sidebar and places notifications in the header", async () => {
    mount();

    const sidebar = screen.getByRole("complementary");
    expect(within(sidebar).getByText("Admin User")).toBeInTheDocument();
    expect(screen.getAllByText("Admin User")).toHaveLength(1);
    expect(within(sidebar).getByText("admin@example.test")).toBeInTheDocument();
    expect(screen.getAllByText("admin@example.test")).toHaveLength(1);
    expect(within(sidebar).getByRole("button", { name: "Keluar" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Buka notifikasi" })).toBeInTheDocument();
    expect(within(sidebar).queryByRole("link", { name: "Notifikasi" })).not.toBeInTheDocument();

    await userEvent.click(within(sidebar).getByRole("button", { name: "Keluar" }));
    expect(state.clear).toHaveBeenCalledOnce();
    expect(await screen.findByText("Login page")).toBeInTheDocument();
  });

  it("does not show the superadmin notifications link for lecturers", () => {
    state.user = { id: "lecturer-1", email: "dosen@example.test", full_name: "Dosen", role: "lecturer", is_active: true };
    mount();

    expect(screen.queryByRole("link", { name: "Buka notifikasi" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Notifikasi" })).not.toBeInTheDocument();
    expect(screen.getByRole("complementary")).toHaveTextContent("Dosen");
  });
});
