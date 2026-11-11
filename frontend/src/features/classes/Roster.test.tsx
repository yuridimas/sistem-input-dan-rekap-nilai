import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import api from "@/lib/api";
import { Roster } from "./Roster";

vi.mock("@/lib/api", () => ({ default: { get: vi.fn(), post: vi.fn(), delete: vi.fn() } }));
vi.mock("@/features/auth/useAuth", () => ({ useAuth: () => ({ user: { id: "lecturer", role: "lecturer" } }) }));
const roster = [
  { id: "enrollment-1", student: { id: "student-1", nim: "001", full_name: "Budi", email: "budi@example.test" } },
  { id: "enrollment-2", student: { id: "student-2", nim: "002", full_name: "Ani", email: null } },
];
function mount(locked = false) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  const tree = (nextLocked: boolean, classId = "class-1") => <QueryClientProvider client={client}><MemoryRouter><Roster classId={classId} locked={nextLocked} /></MemoryRouter></QueryClientProvider>;
  const view = render(tree(locked));
  return { rerenderRoster: (nextLocked: boolean, classId?: string) => view.rerender(tree(nextLocked, classId)) };
}
beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.get).mockImplementation(async (path) => ({ data: path === "/students" ? roster.map((row) => row.student) : roster }));
  vi.mocked(api.post).mockResolvedValue({ data: roster[0] });
  vi.mocked(api.delete).mockResolvedValue({ data: undefined });
});
describe("class roster table", () => {
  it("sorts names and retains removal while unlocked", async () => {
    mount();
    await screen.findByText("Budi");
    await userEvent.click(screen.getByRole("button", { name: "Mahasiswa" }));
    expect(screen.getAllByRole("row")[1]).toHaveTextContent("Ani");
    expect(screen.getByRole("button", { name: "Keluarkan Budi" })).toBeInTheDocument();
  });
  it("searches name NIM and email locally and retains search on refresh", async () => {
    mount();
    await screen.findByText("Budi");
    const search = screen.getByRole("searchbox", { name: "Cari" });
    for (const term of ["Budi", "001", "budi@"]) {
      await userEvent.clear(search);
      await userEvent.type(search, term);
      expect(screen.getByText("Budi")).toBeInTheDocument();
      expect(screen.queryByText("Ani")).not.toBeInTheDocument();
    }
    expect(api.get).toHaveBeenCalledTimes(1);
    await userEvent.click(screen.getByRole("button", { name: "Segarkan" }));
    await waitFor(() => expect(api.get).toHaveBeenCalledTimes(2));
    expect(search).toHaveValue("budi@");
    expect(api.get).toHaveBeenLastCalledWith("/classes/class-1/roster");
    await userEvent.type(search, "tidak-cocok");
    expect(screen.getByRole("status")).toHaveTextContent("Tidak ada mahasiswa yang cocok dengan pencarian.");
  });
  it("keeps detail readable when locked and disables enrollment changes", async () => {
    mount(true);
    expect(await screen.findByRole("link", { name: "Lihat mahasiswa Budi (001)" })).toHaveAttribute("href", "/students/student-1");
    expect(screen.queryByRole("link", { name: "Budi" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Keluarkan Budi" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Tambah mahasiswa ke kelas" })).toBeDisabled();
    expect(screen.getByRole("columnheader", { name: "Tindakan" })).toBeInTheDocument();
  });
  it.each(["add", "remove"])("closes an open %s dialog when class becomes locked", async (action) => {
    const view = mount();
    await screen.findByText("Budi");
    await userEvent.click(screen.getByRole("button", { name: action === "add" ? "Tambah mahasiswa ke kelas" : "Keluarkan Budi" }));
    expect(await screen.findByRole("dialog")).toBeInTheDocument();
    view.rerenderRoster(true);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Lihat mahasiswa Budi (001)" })).toBeInTheDocument();
    expect(api.post).not.toHaveBeenCalled();
    expect(api.delete).not.toHaveBeenCalled();
  });
  it("reuses an existing NIM without replacing the student profile", async () => {
    mount();
    await userEvent.click(await screen.findByRole("button", { name: "Tambah mahasiswa ke kelas" }));
    const dialog = await screen.findByRole("dialog");
    await userEvent.type(within(dialog).getByLabelText("NIM"), "001");
    await within(dialog).findByText("Budi");
    await userEvent.click(within(dialog).getByRole("button", { name: "Daftarkan mahasiswa" }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith("/classes/class-1/enrollments", { nim: "001" }));
  });
  it("sends profile fields when enrolling a new student", async () => {
    mount();
    await userEvent.click(await screen.findByRole("button", { name: "Tambah mahasiswa ke kelas" }));
    const dialog = await screen.findByRole("dialog");
    await userEvent.type(within(dialog).getByLabelText("NIM"), "003");
    await userEvent.type(await within(dialog).findByLabelText("Nama lengkap mahasiswa baru"), "Dewi");
    await userEvent.type(within(dialog).getByLabelText("Email (opsional)"), "dewi@example.test");
    await userEvent.click(within(dialog).getByRole("button", { name: "Daftarkan mahasiswa" }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith("/classes/class-1/enrollments", { nim: "003", full_name: "Dewi", email: "dewi@example.test" }));
  });
  it("removes by enrollment ID and displays conflicts while refreshing roster", async () => {
    vi.mocked(api.delete).mockRejectedValue({ isAxiosError: true, response: { status: 409, data: { detail: "Roster telah terkunci" } } });
    mount();
    await userEvent.click(await screen.findByRole("button", { name: "Keluarkan Budi" }));
    const dialog = await screen.findByRole("dialog");
    await userEvent.click(within(dialog).getByRole("button", { name: "Keluarkan mahasiswa" }));
    expect(await within(dialog).findByText("Roster telah terkunci")).toBeInTheDocument();
    expect(api.delete).toHaveBeenCalledWith("/classes/class-1/enrollments/enrollment-1");
    await waitFor(() => expect(api.get).toHaveBeenCalledTimes(2));
  });
  it("paginates and renders null or long emails", async () => {
    const longEmail = "student.with.a.long.email.for.layout@academic.example.test";
    vi.mocked(api.get).mockResolvedValue({ data: Array.from({ length: 12 }, (_, i) => ({ id: "e" + i, student: { ...roster[0].student, id: "s" + i, full_name: "Mahasiswa " + i, email: i ? null : longEmail } })) });
    mount();
    expect(await screen.findByText(longEmail)).toBeInTheDocument();
    expect(screen.getByRole("row", { name: /Mahasiswa 1 001/ })).toHaveTextContent("—");
    await userEvent.click(screen.getByRole("button", { name: "Halaman berikutnya" }));
    expect(screen.getByText("Mahasiswa 11")).toBeInTheDocument();
    await userEvent.type(screen.getByRole("searchbox", { name: "Cari" }), "Mahasiswa 0");
    expect(await screen.findByText("Mahasiswa 0")).toBeInTheDocument();
  });
  it("switches query and removal to the current class", async () => {
    const view = mount();
    await screen.findByText("Budi");
    view.rerenderRoster(false, "class-2");
    await waitFor(() => expect(api.get).toHaveBeenLastCalledWith("/classes/class-2/roster"));
    await userEvent.click(await screen.findByRole("button", { name: "Keluarkan Budi" }));
    await userEvent.click(screen.getByRole("button", { name: "Keluarkan mahasiswa" }));
    await waitFor(() => expect(api.delete).toHaveBeenCalledWith("/classes/class-2/enrollments/enrollment-1"));
  });
  it.each(["empty", "pending", "error"])("keeps controls for %s data", async (state) => {
    if (state === "empty") vi.mocked(api.get).mockResolvedValue({ data: [] });
    if (state === "pending") vi.mocked(api.get).mockImplementation(() => new Promise(() => {}));
    if (state === "error") vi.mocked(api.get).mockRejectedValue(new Error("offline"));
    mount();
    if (state === "error") await screen.findByRole("alert");
    expect(screen.getByRole("searchbox", { name: "Cari" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Segarkan" })).toBeInTheDocument();
  });
});
