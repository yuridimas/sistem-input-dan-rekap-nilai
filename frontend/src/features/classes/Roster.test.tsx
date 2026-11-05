import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { Roster } from "./Roster";

const state = vi.hoisted(() => ({
  roster: [
    { id: "e1", student: { id: "s1", nim: "001", full_name: "Budi", email: "budi@example.test" } },
    { id: "e2", student: { id: "s2", nim: "002", full_name: "Ani", email: "ani@example.test" } },
  ],
}));

vi.mock("@/features/academic/api", () => ({
  useAcademicQuery: () => ({ data: state.roster, isPending: false, error: null }),
}));

function mount(locked: boolean) {
  return render(<MemoryRouter><Roster classId="class-1" locked={locked} /></MemoryRouter>);
}

beforeEach(() => {
  state.roster = [
    { id: "e1", student: { id: "s1", nim: "001", full_name: "Budi", email: "budi@example.test" } },
    { id: "e2", student: { id: "s2", nim: "002", full_name: "Ani", email: "ani@example.test" } },
  ];
});

describe("class roster data table", () => {
  it("sorts roster names and keeps enrollment removal available while unlocked", async () => {
    mount(false);

    await userEvent.click(screen.getByRole("button", { name: "Mahasiswa" }));
    expect(screen.getAllByRole("row")[1]).toHaveTextContent("Ani");
    expect(screen.getByRole("button", { name: "Keluarkan Budi" })).toBeInTheDocument();
  });

  it("hides row removal and disables adding when the class is locked", () => {
    mount(true);

    expect(screen.queryByRole("button", { name: "Keluarkan Budi" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Tambah mahasiswa ke kelas/ })).toBeDisabled();
  });
});
