/**
 * Integration test grid, hook, dan guard navigasi dengan server API palsu.
 * Urutan save/finalisasi serta perpindahan tab diuji dari perilaku pengguna, bukan DB nyata.
 */
import {
  act,
  fireEvent,
  render,
  renderHook,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  createMemoryRouter,
  Link,
  RouterProvider,
  useSearchParams,
} from "react-router-dom";
import { GradeEntryGrid } from "./GradeEntryGrid";
import { GradeNavigationGuard } from "./GradeNavigationGuard";
import { useGradeEntry } from "./hooks";
import type { GradeGrid, SavedGrade } from "./types";
import api from "@/lib/api";
import { ClassDetailPage } from "@/features/classes/ClassDetailPage";

vi.mock("@/lib/api", () => ({
  default: { get: vi.fn(), put: vi.fn(), post: vi.fn() },
}));
vi.mock("@/features/auth/useAuth", () => ({
  useAuth: () => ({ user: { id: "user" }, hasTokens: true }),
}));
let server: GradeGrid;
const initial: GradeGrid = {
  class_id: "class",
  components: [
    {
      id: "uts",
      name: "UTS",
      category: "uts",
      weight: "50",
      max_score: "100",
      order_index: 0,
    },
    {
      id: "uas",
      name: "UAS",
      category: "uas",
      weight: "50",
      max_score: "100",
      order_index: 1,
    },
  ],
  grades: [
    {
      enrollment_id: "e1",
      student: { id: "s1", nim: "001", full_name: "Satu", email: null },
      scores: {},
      final_score: null,
      status: "draft",
    },
  ],
};
const saved: SavedGrade = {
  enrollment_id: "e1",
  final_score: "40",
  status: "draft",
};
/**
 * Pertahankan hook ketika panel tab berubah agar test dapat mendeteksi draft yang hilang.
 */
function Harness() {
  const [params] = useSearchParams();
  const entry = useGradeEntry("class", true);
  return (
    <>
      <Link to="/other">Halaman lain</Link>
      <Link to="?tab=students">Tab mahasiswa</Link>
      <Link to="?tab=grades">Tab nilai</Link>
      {params.get("tab") === "students" ? (
        <p>Panel mahasiswa</p>
      ) : (
        <GradeEntryGrid entry={entry} />
      )}
      <GradeNavigationGuard entry={entry} classId="class" />
    </>
  );
}
/**
 * Pasang router dan cache baru agar navigasi serta pending request terisolasi per skenario.
 */
function mount() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  const router = createMemoryRouter(
    [
      { path: "/classes/:id", element: <Harness /> },
      { path: "/other", element: <p>Tujuan navigasi</p> },
    ],
    { initialEntries: ["/classes/class?tab=grades"] },
  );
  render(
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}
beforeEach(() => {
  vi.clearAllMocks();
  server = structuredClone(initial);
  vi.mocked(api.get).mockImplementation(async () => ({
    data: structuredClone(server),
  }));
  vi.mocked(api.put).mockImplementation(async (_url, payload) => {
    const scores = { ...server.grades[0].scores };
    for (const [key, value] of Object.entries(
      payload as Record<string, string | null>,
    )) {
      if (value === null) delete scores[key];
      else scores[key] = value;
    }
    server.grades[0] = { ...server.grades[0], scores, final_score: "40" };
    return { data: saved };
  });
});

describe("grade entry interactions", () => {
  it("applies a post-save refresh even when structural sharing reuses its data identity", async () => {
    let finish!: (value: { data: SavedGrade }) => void;
    vi.mocked(api.put).mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          finish = resolve;
        }),
    );
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false, gcTime: 0 } },
    });
    const { result } = renderHook(() => useGradeEntry("class", true), {
      wrapper: ({ children }) => (
        <QueryClientProvider client={client}>{children}</QueryClientProvider>
      ),
    });
    await waitFor(() => expect(result.current.snapshot.data).not.toBeNull());
    act(() => {
      result.current.engine.edit("e1", "uts", "80");
      void result.current.engine.queue("e1");
    });
    server.grades[0] = {
      ...server.grades[0],
      scores: { uts: "80", uas: "70" },
      status: "finalized",
      final_score: "75",
    };
    await act(async () => {
      await client.refetchQueries({
        queryKey: ["academic", "user", "/classes/class/grades"],
      });
    });
    expect(result.current.snapshot.data!.grades[0].status).toBe("draft");
    await act(async () => {
      finish({ data: saved });
    });
    await waitFor(() => expect(result.current.snapshot.saving).toBe(false));
    await waitFor(() =>
      expect(result.current.snapshot.data!.grades[0].status).toBe("finalized"),
    );
    expect(result.current.snapshot.cells["e1/uas"].value).toBe("70");
  });
  it("retains the navigation guard after a background class metadata error", async () => {
    let failClass = false;
    vi.mocked(api.get).mockImplementation(async (path) => {
      if (path === "/classes/class") {
        if (failClass) throw new Error("metadata offline");
        return {
          data: {
            id: "class",
            course_id: "course",
            section: "A",
            academic_year: "2026/2027",
            lecturer_id: "user",
            has_finalized_grades: false,
          },
        };
      }
      if (path === "/courses/course")
        return { data: { id: "course", code: "IF1", name: "Course" } };
      return { data: structuredClone(server) };
    });
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false, gcTime: 0 } },
    });
    const router = createMemoryRouter(
      [
        { path: "/classes/:classId", element: <ClassDetailPage /> },
        { path: "/other", element: <p>Tujuan navigasi</p> },
      ],
      { initialEntries: ["/classes/class?tab=grades"] },
    );
    render(
      <QueryClientProvider client={client}>
        <RouterProvider router={router} />
      </QueryClientProvider>,
    );
    fireEvent.change(await screen.findByLabelText("001 Satu — UTS"), {
      target: { value: "101" },
    });
    failClass = true;
    await act(async () => {
      await client.invalidateQueries({
        queryKey: ["academic", "user", "/classes/class"],
      });
    });
    await screen.findByRole("button", { name: "Coba lagi" });
    const event = new Event("beforeunload", { cancelable: true });
    window.dispatchEvent(event);
    expect(event.defaultPrevented).toBe(true);
    await act(async () => {
      void router.navigate("/other");
    });
    await screen.findByRole("dialog");
    expect(screen.queryByText("Tujuan navigasi")).not.toBeInTheDocument();
  });
  it("preserves drafts across class tabs without a leave-page prompt", async () => {
    mount();
    fireEvent.change(await screen.findByLabelText("001 Satu — UTS"), {
      target: { value: "101" },
    });
    await userEvent.click(screen.getByRole("link", { name: "Tab mahasiswa" }));
    await screen.findByText("Panel mahasiswa");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("link", { name: "Tab nilai" }));
    expect(await screen.findByLabelText("001 Satu — UTS")).toHaveValue("101");
  });

  it("checks an uncertain release instead of automatically submitting it again", async () => {
    server.grades[0].scores = { uts: "80", uas: "0" };
    vi.mocked(api.post).mockImplementation(async () => {
      server.grades[0].status = "finalized";
      throw Object.assign(new Error("connection lost"), { isAxiosError: true });
    });
    mount();
    await screen.findByLabelText("001 Satu — UTS");
    await userEvent.click(
      screen.getByRole("button", { name: "Finalisasi & Rilis" }),
    );
    await userEvent.click(
      await screen.findByRole("button", { name: "Konfirmasi rilis" }),
    );
    const check = await screen.findByRole("button", {
      name: "Periksa status rilis",
    });
    expect(screen.getByLabelText("001 Satu — UTS")).toBeDisabled();
    expect(api.post).toHaveBeenCalledTimes(1);
    await userEvent.click(check);
    await screen.findByText(
      "Seluruh nilai kelas sudah dirilis. Status terbaru telah dimuat.",
    );
    expect(api.post).toHaveBeenCalledTimes(1);
    expect(screen.getByLabelText("001 Satu — UTS")).toBeDisabled();
  });
  it("retains newer typing while an older autosave is pending", async () => {
    let finish!: (value: { data: SavedGrade }) => void;
    vi.mocked(api.put).mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          finish = resolve;
        }),
    );
    mount();
    const input = await screen.findByLabelText("001 Satu — UTS");
    fireEvent.change(input, { target: { value: "80" } });
    fireEvent.blur(input);
    await waitFor(() => expect(api.put).toHaveBeenCalledTimes(1));
    fireEvent.change(input, { target: { value: "90" } });
    fireEvent.blur(input);
    await act(async () => {
      finish({ data: saved });
    });
    await waitFor(() => expect(api.put).toHaveBeenCalledTimes(2));
    expect(input).toHaveValue("90");
    expect(vi.mocked(api.put).mock.calls[1][1]).toEqual({ uts: "90" });
  });

  it("keeps failed input and retries only when requested", async () => {
    vi.mocked(api.put).mockRejectedValueOnce(new Error("offline"));
    mount();
    const input = await screen.findByLabelText("001 Satu — UTS");
    fireEvent.change(input, { target: { value: "80" } });
    fireEvent.blur(input);
    await screen.findByText("Gagal disimpan", { exact: true });
    expect(input).toHaveValue("80");
    expect(api.put).toHaveBeenCalledTimes(1);
    await userEvent.click(screen.getByRole("button", { name: "Simpan semua" }));
    await waitFor(() => expect(api.put).toHaveBeenCalledTimes(2));
  });

  it("waits for saving, shows missing cells and releases only after confirmation", async () => {
    let finish!: (value: { data: SavedGrade }) => void;
    vi.mocked(api.put).mockImplementationOnce(
      (_url, payload) =>
        new Promise((resolve) => {
          finish = (value) => {
            server.grades[0].scores = {
              ...(payload as Record<string, string>),
            };
            resolve(value);
          };
        }),
    );
    vi.mocked(api.post).mockImplementation(async () => {
      server.grades[0].status = "finalized";
      return { data: { finalized_count: 1, notified: 0 } };
    });
    mount();
    const input = await screen.findByLabelText("001 Satu — UTS");
    fireEvent.change(input, { target: { value: "80" } });
    fireEvent.blur(input);
    await userEvent.click(
      screen.getByRole("button", { name: "Finalisasi & Rilis" }),
    );
    expect(api.post).not.toHaveBeenCalled();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    await act(async () => {
      finish({ data: saved });
    });
    const missing = await screen.findByRole("button", { name: "001 — UAS" });
    expect(
      screen.getByRole("button", { name: "Konfirmasi rilis" }),
    ).toBeDisabled();
    await userEvent.click(missing);
    await waitFor(() =>
      expect(screen.getByLabelText("001 Satu — UAS")).toHaveFocus(),
    );
    fireEvent.change(screen.getByLabelText("001 Satu — UAS"), {
      target: { value: "0" },
    });
    fireEvent.blur(screen.getByLabelText("001 Satu — UAS"));
    await userEvent.click(
      screen.getByRole("button", { name: "Finalisasi & Rilis" }),
    );
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Konfirmasi rilis" }),
      ).toBeEnabled(),
    );
    expect(api.post).not.toHaveBeenCalled();
    await userEvent.click(
      screen.getByRole("button", { name: "Konfirmasi rilis" }),
    );
    await screen.findByText(/1 mahasiswa berhasil dirilis/);
    expect(api.post).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(input).toBeDisabled());
  });

  it("protects unsaved invalid drafts during navigation and refresh", async () => {
    mount();
    const input = await screen.findByLabelText("001 Satu — UTS");
    fireEvent.change(input, { target: { value: "101" } });
    const event = new Event("beforeunload", { cancelable: true });
    window.dispatchEvent(event);
    expect(event.defaultPrevented).toBe(true);
    await userEvent.click(screen.getByRole("link", { name: "Halaman lain" }));
    await screen.findByRole("dialog");
    await userEvent.click(
      screen.getByRole("button", { name: "Tetap di kelas" }),
    );
    expect(input).toHaveValue("101");
    await userEvent.click(screen.getByRole("link", { name: "Halaman lain" }));
    await userEvent.click(
      screen.getByRole("button", { name: "Buang perubahan" }),
    );
    await screen.findByText("Tujuan navigasi");
    expect(api.put).not.toHaveBeenCalled();
  });
});
