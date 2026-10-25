import { describe, expect, it, vi } from "vitest";
import { GradeDraft, GradeSaveError, cellKey, validateScore } from "./draft";
import type { GradeGrid, SavedGrade } from "./types";

export const grid: GradeGrid = {
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
const saved = (score = "40"): SavedGrade => ({
  enrollment_id: "e1",
  final_score: score,
  status: "draft",
});
function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: Error) => void;
  const promise = new Promise<T>((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
}

describe("score validation", () => {
  it("distinguishes blank, zero and Indonesian decimals", () => {
    expect(validateScore("", "100")).toBeNull();
    expect(validateScore("0", "100")).toBeNull();
    expect(validateScore("33,33", "100")).toBeNull();
    for (const value of ["-1", "100.01", "0.001", "NaN", "Infinity", "1e2"])
      expect(validateScore(value, "100")).toBeTruthy();
  });
});

describe("serialized draft writes", () => {
  it("does not treat equivalent decimal representations as unsaved", async () => {
    const write = vi.fn();
    const draft = new GradeDraft(write);
    draft.receive({
      ...grid,
      grades: [{ ...grid.grades[0], scores: { uts: "80.00" } }],
    });
    draft.edit("e1", "uts", "80,0");
    expect(draft.hasChanges()).toBe(false);
    await draft.queue("e1");
    expect(write).not.toHaveBeenCalled();
  });
  it("preserves edits made during an older request and queues the latest version", async () => {
    const first = deferred<SavedGrade>();
    const second = deferred<SavedGrade>();
    const write = vi
      .fn()
      .mockReturnValueOnce(first.promise)
      .mockReturnValueOnce(second.promise);
    const draft = new GradeDraft(write);
    draft.receive(grid);
    draft.edit("e1", "uts", "80");
    const work = draft.queue("e1");
    draft.edit("e1", "uts", "90");
    void draft.queue("e1");
    expect(write).toHaveBeenCalledTimes(1);
    first.resolve(saved());
    await vi.waitFor(() => expect(write).toHaveBeenCalledTimes(2));
    expect(draft.getSnapshot().cells[cellKey("e1", "uts")].value).toBe("90");
    expect(write.mock.calls[1][1]).toEqual({ uts: "90" });
    second.resolve(saved("45"));
    await work;
    expect(draft.hasChanges()).toBe(false);
    expect(draft.getSnapshot().data!.grades[0].final_score).toBe("45");
  });

  it("sends only changed cells, including null for clearing and numeric zero", async () => {
    const write = vi.fn().mockResolvedValue(saved("0"));
    const draft = new GradeDraft(write);
    draft.receive({
      ...grid,
      grades: [{ ...grid.grades[0], scores: { uts: "80" } }],
    });
    draft.edit("e1", "uts", "");
    draft.edit("e1", "uas", "0");
    expect(await draft.flush()).toBe(true);
    expect(write).toHaveBeenCalledWith("e1", { uts: null, uas: "0" });
  });

  it("retains failed drafts without automatic retry; flush explicitly retries", async () => {
    const write = vi
      .fn()
      .mockRejectedValueOnce(new Error("Jaringan gagal"))
      .mockResolvedValue(saved());
    const draft = new GradeDraft(write);
    draft.receive(grid);
    draft.edit("e1", "uts", "80");
    await draft.queue("e1");
    await draft.queue("e1");
    expect(write).toHaveBeenCalledTimes(1);
    expect(draft.hasChanges()).toBe(true);
    expect(
      draft.getSnapshot().cells[cellKey("e1", "uts")].failure,
    ).toBeTruthy();
    expect(await draft.flush()).toBe(true);
    expect(write).toHaveBeenCalledTimes(2);
  });

  it("does not send invalid input or consider it ready for finalization", async () => {
    const write = vi.fn();
    const draft = new GradeDraft(write);
    draft.receive(grid);
    draft.edit("e1", "uts", "101");
    expect(await draft.flush()).toBe(false);
    expect(write).not.toHaveBeenCalled();
  });

  it("merges pristine cells but preserves dirty cells on background refresh", () => {
    const draft = new GradeDraft(vi.fn());
    draft.receive(grid);
    draft.edit("e1", "uts", "80");
    draft.receive({
      ...grid,
      grades: [{ ...grid.grades[0], scores: { uts: "50", uas: "70" } }],
    });
    expect(draft.getSnapshot().cells[cellKey("e1", "uts")].value).toBe("80");
    expect(draft.getSnapshot().cells[cellKey("e1", "uas")].value).toBe("70");
  });

  it("ignores stale score refreshes while writing", async () => {
    const pending = deferred<SavedGrade>();
    const draft = new GradeDraft(() => pending.promise);
    draft.receive(grid);
    draft.edit("e1", "uts", "80");
    const work = draft.queue("e1");
    draft.receive(grid);
    pending.resolve(saved());
    await work;
    expect(draft.getSnapshot().cells[cellKey("e1", "uts")].saved).toBe("80");
    expect(draft.hasChanges()).toBe(false);
  });

  it("pauses on structural changes rather than losing local edits", async () => {
    const write = vi.fn();
    const draft = new GradeDraft(write);
    draft.receive(grid);
    draft.edit("e1", "uts", "80");
    draft.receive({ ...grid, components: grid.components.slice(1) });
    expect(draft.getSnapshot().paused).toBe(true);
    expect(await draft.flush()).toBe(false);
    expect(write).not.toHaveBeenCalled();
    expect(draft.getSnapshot().cells[cellKey("e1", "uts")].value).toBe("80");
  });

  it("keeps a structural pause when an outstanding write later fails", async () => {
    const pending = deferred<SavedGrade>();
    const draft = new GradeDraft(() => pending.promise);
    draft.receive(grid);
    draft.edit("e1", "uts", "80");
    const work = draft.queue("e1");
    draft.receive({ ...grid, components: grid.components.slice(1) });
    expect(draft.getSnapshot().paused).toBe(true);
    pending.reject(new GradeSaveError("Komponen berubah", 422));
    await work;
    expect(draft.getSnapshot().paused).toBe(true);
  });

  it("adopts concurrent finalization and prevents further edits", () => {
    const draft = new GradeDraft(vi.fn());
    draft.receive(grid);
    draft.edit("e1", "uts", "80");
    draft.receive({
      ...grid,
      grades: [
        {
          ...grid.grades[0],
          scores: { uts: "50", uas: "60" },
          status: "finalized",
          final_score: "55",
        },
      ],
    });
    draft.edit("e1", "uts", "100");
    expect(draft.getSnapshot().cells[cellKey("e1", "uts")].value).toBe("50");
    expect(draft.hasChanges()).toBe(false);
    expect(draft.getSnapshot().warning).toBeTruthy();
  });

  it("waits for outstanding saves before flush can report completion", async () => {
    const pending = deferred<SavedGrade>();
    const draft = new GradeDraft(() => pending.promise);
    draft.receive(grid);
    draft.edit("e1", "uts", "80");
    void draft.queue("e1");
    let finished = false;
    const flush = draft.flush().then(() => {
      finished = true;
    });
    await Promise.resolve();
    expect(finished).toBe(false);
    pending.resolve(saved());
    await flush;
    expect(finished).toBe(true);
  });

  it("pauses after access loss", async () => {
    const draft = new GradeDraft(async () => {
      throw new GradeSaveError("Tidak memiliki akses", 403);
    });
    draft.receive(grid);
    draft.edit("e1", "uts", "80");
    expect(await draft.flush()).toBe(false);
    expect(draft.getSnapshot().paused).toBe(true);
  });

  it("stops queued writes when its page is detached", async () => {
    const pending = deferred<SavedGrade>();
    const write = vi.fn().mockReturnValue(pending.promise);
    const draft = new GradeDraft(write);
    draft.receive(grid);
    draft.edit("e1", "uts", "80");
    const work = draft.queue("e1");
    draft.edit("e1", "uts", "90");
    void draft.queue("e1");
    draft.detach();
    pending.resolve(saved());
    await work;
    expect(write).toHaveBeenCalledTimes(1);
  });
});
