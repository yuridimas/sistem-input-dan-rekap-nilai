import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { StudentsPage } from "./StudentsPage";

const state = vi.hoisted(() => ({
  user: { id: "lecturer-1", role: "lecturer" as "lecturer" | "superadmin" },
  students: [] as Array<{ id: string; nim: string; full_name: string; email: string | null }>,
}));

vi.mock("@/features/auth/useAuth", () => ({ useAuth: () => ({ user: state.user }) }));
vi.mock("@/features/academic/api", () => ({
  useAcademicQuery: () => ({ data: state.students, isPending: false, error: null }),
}));

function mount() {
  return render(<MemoryRouter><StudentsPage /></MemoryRouter>);
}

beforeEach(() => {
  state.user = { id: "lecturer-1", role: "lecturer" };
  state.students = [
    { id: "s1", nim: "001", full_name: "Budi", email: "budi@example.test" },
    { id: "s2", nim: "002", full_name: "Ani", email: "ani@example.test" },
  ];
});

describe("students page data table", () => {
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
