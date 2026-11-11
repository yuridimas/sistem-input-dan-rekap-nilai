import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import api from "@/lib/api";
import { CoursesPage } from "./CoursesPage";

vi.mock("@/lib/api", () => ({ default: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() } }));
const auth = vi.hoisted(() => ({ user: { id: "owner", role: "lecturer" as "lecturer" | "superadmin" } }));
vi.mock("@/features/auth/useAuth", () => ({ useAuth: () => auth }));

const courses = [
  { id: "c1", code: "IF101", name: "Pemrograman Dasar", credits: 3, semester: "2026/1", created_by: "owner" },
  { id: "c2", code: "IF202", name: "Basis Data", credits: 2, semester: "2026/2", created_by: "another" },
];

function mount() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  return render(<QueryClientProvider client={client}><MemoryRouter><CoursesPage /></MemoryRouter></QueryClientProvider>);
}

beforeEach(() => {
  vi.clearAllMocks();
  auth.user = { id: "owner", role: "lecturer" };
  vi.mocked(api.get).mockResolvedValue({ data: courses });
});

describe("courses index", () => {
  it("filters courses by name or code through the Cari input without another request", async () => {
    mount();
    await screen.findByRole("link", { name: "Pemrograman Dasar" });
    const search = screen.getByRole("searchbox", { name: "Cari" });
    await userEvent.type(search, "Basis");
    expect(screen.getByRole("link", { name: "Basis Data" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Pemrograman Dasar" })).not.toBeInTheDocument();
    await userEvent.clear(search);
    await userEvent.type(search, "IF101");
    expect(screen.getByRole("link", { name: "Pemrograman Dasar" })).toHaveAttribute("href", "/courses/c1");
    expect(screen.queryByRole("link", { name: "Basis Data" })).not.toBeInTheDocument();
    expect(api.get).toHaveBeenCalledTimes(1);
  });

  it("refreshes courses from the table toolbar", async () => {
    mount();
    await screen.findByRole("link", { name: "Basis Data" });
    await userEvent.click(screen.getByRole("button", { name: "Segarkan" }));
    await waitFor(() => expect(api.get).toHaveBeenCalledTimes(2));
  });

  it("keeps create and row actions connected to existing dialogs", async () => {
    mount();
    await screen.findByRole("link", { name: "Pemrograman Dasar" });
    await userEvent.click(screen.getByRole("button", { name: "Tambah mata kuliah" }));
    expect(await screen.findByRole("dialog", { name: "Tambah mata kuliah" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Batal" }));
    await userEvent.click(screen.getByRole("button", { name: "Edit Pemrograman Dasar" }));
    const edit = await screen.findByRole("dialog", { name: "Edit mata kuliah" });
    expect(within(edit).getByLabelText("Nama mata kuliah")).toHaveValue("Pemrograman Dasar");
    await userEvent.click(within(edit).getByRole("button", { name: "Batal" }));
    await userEvent.click(screen.getByRole("button", { name: "Hapus Pemrograman Dasar" }));
    expect(await screen.findByRole("dialog", { name: "Hapus mata kuliah" })).toHaveTextContent("Pemrograman Dasar");
  });

  it("restricts row actions to the lecturer's own courses", async () => {
    mount();
    await screen.findByRole("link", { name: "Basis Data" });
    expect(screen.getByRole("button", { name: "Edit Pemrograman Dasar" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Edit Basis Data" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Hapus Basis Data" })).not.toBeInTheDocument();
  });

  it("allows superadmins to act on courses owned by another lecturer", async () => {
    auth.user = { id: "admin", role: "superadmin" };
    mount();
    expect(await screen.findByRole("button", { name: "Edit Basis Data" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Hapus Basis Data" })).toBeInTheDocument();
  });

  it.each(["empty", "pending", "error"])("keeps table controls available for %s data", async (state) => {
    if (state === "empty") vi.mocked(api.get).mockResolvedValue({ data: [] });
    if (state === "pending") vi.mocked(api.get).mockImplementation(() => new Promise(() => {}));
    if (state === "error") vi.mocked(api.get).mockRejectedValue(new Error("offline"));
    mount();
    if (state === "error") await screen.findByRole("alert");
    expect(screen.getByRole("searchbox", { name: "Cari" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Segarkan" })).toBeInTheDocument();
  });
});
