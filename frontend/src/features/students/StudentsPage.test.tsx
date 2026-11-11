import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { StudentsPage } from "./StudentsPage";

const state = vi.hoisted(() => ({
  user: { id: "lecturer-1", role: "lecturer" as "lecturer" | "superadmin" },
  students: [] as Array<{ id: string; nim: string; full_name: string; email: string | null }>,
  refetch: vi.fn(),
  isPending: false,
  error: null as unknown,
}));

vi.mock("@/features/auth/useAuth", () => ({ useAuth: () => ({ user: state.user }) }));
vi.mock("@/features/academic/api", async (importOriginal) => ({
  ...await importOriginal<typeof import("@/features/academic/api")>(),
  useAcademicQuery: () => ({ data: state.students, isPending: state.isPending, error: state.error, isFetching: state.isPending, refetch: state.refetch }),
}));

function mount() {
  return render(<MemoryRouter><StudentsPage /></MemoryRouter>);
}

beforeEach(() => {
  vi.clearAllMocks();
  state.isPending = false;
  state.error = null;
  state.user = { id: "lecturer-1", role: "lecturer" };
  state.students = [
    { id: "s1", nim: "001", full_name: "Budi", email: "budi@example.test" },
    { id: "s2", nim: "002", full_name: "Ani", email: "ani@example.test" },
  ];
});

describe("students page data table", () => {
  it("searches names and NIM through the Cari input", async () => {
    mount();
    const search = screen.getByRole("searchbox", { name: "Cari" });
    await userEvent.type(search, "Ani");
    expect(screen.getByRole("link", { name: "Ani" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Budi" })).not.toBeInTheDocument();
    await userEvent.clear(search);
    await userEvent.type(search, "001");
    expect(screen.getByRole("link", { name: "Budi" })).toHaveAttribute("href", "/students/s1");
    expect(screen.queryByRole("link", { name: "Ani" })).not.toBeInTheDocument();
    expect(state.refetch).not.toHaveBeenCalled();
  });

  it("refreshes students from the table toolbar", async () => {
    mount();
    await userEvent.click(screen.getByRole("button", { name: "Segarkan" }));
    expect(state.refetch).toHaveBeenCalledTimes(1);
  });

  it("renders long and missing student emails", () => {
    state.students[0].email = "student.with.a.very.long.email.address@academic.example.test";
    state.students[1].email = null;
    mount();
    expect(screen.getByRole("row", { name: /Budi/ })).toHaveTextContent(state.students[0].email);
    expect(screen.getByRole("row", { name: /Ani/ })).toHaveTextContent("—");
  });

  it.each(["empty", "pending", "error"])("keeps table controls available for %s data", (status) => {
    state.students = [];
    state.isPending = status === "pending";
    state.error = status === "error" ? new Error("offline") : null;
    mount();
    expect(screen.getByRole("searchbox", { name: "Cari" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Segarkan" })).toBeInTheDocument();
  });

  it("sorts student names and retains the lecturer action restrictions", async () => {
    mount();

    await userEvent.click(screen.getByRole("button", { name: "Mahasiswa" }));
    expect(screen.getAllByRole("row")[1]).toHaveTextContent("Ani");
    expect(screen.queryByRole("button", { name: "Edit Ani" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Hapus Ani" })).not.toBeInTheDocument();
  });

  it("shows edit actions to superadmins", () => {
    state.user = { id: "admin-1", role: "superadmin" };
    mount();

    expect(screen.getByRole("button", { name: "Edit Budi" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Hapus Budi" })).toBeInTheDocument();
  });
});
