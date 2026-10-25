import type { GradeGrid, SavedGrade, ScoreChanges } from "./types";

export const cellKey = (enrollment: string, component: string) =>
  `${enrollment}/${component}`;
const decimal = /^(?:\d+(?:\.\d{0,2})?|\.\d{1,2})$/;
const textNumber = (value: string) => value.trim().replace(",", ".");
const canonical = (value: string) => {
  const text = textNumber(value);
  return text === ""
    ? ""
    : decimal.test(text)
      ? String(Number(text))
      : `invalid:${value}`;
};

export function validateScore(value: string, maximum: string): string | null {
  const text = textNumber(value);
  if (text === "") return null;
  if (!decimal.test(text)) return "Gunakan angka dengan maksimal dua desimal.";
  if (!Number.isFinite(Number(text)) || Number(text) > Number(maximum))
    return `Nilai harus antara 0 dan ${maximum}.`;
  return null;
}

export interface DraftCell {
  value: string;
  saved: string;
  version: number;
  error: string | null;
  failure: string | null;
}
export const cellChanged = (cell: DraftCell) =>
  canonical(cell.value) !== canonical(cell.saved);
export interface DraftSnapshot {
  data: GradeGrid | null;
  cells: Record<string, DraftCell>;
  saving: boolean;
  frozen: boolean;
  paused: boolean;
  error: string | null;
  warning: string | null;
}
export class GradeSaveError extends Error {
  status: number | undefined;
  constructor(message: string, status?: number) {
    super(message);
    this.status = status;
  }
}

function signature(data: GradeGrid) {
  return JSON.stringify([
    data.class_id,
    data.components.map((row) => [
      row.id,
      row.name,
      row.category,
      row.weight,
      row.max_score,
      row.order_index,
    ]),
    data.grades.map((row) => row.enrollment_id).sort(),
  ]);
}

export class GradeDraft {
  private state: DraftSnapshot = {
    data: null,
    cells: {},
    saving: false,
    frozen: false,
    paused: false,
    error: null,
    warning: null,
  };
  private listeners = new Set<() => void>();
  private pending = new Set<string>();
  private work: Promise<void> | null = null;
  private write: (row: string, payload: ScoreChanges) => Promise<SavedGrade>;
  private onIdle?: () => void;
  private active = true;

  constructor(
    write: (row: string, payload: ScoreChanges) => Promise<SavedGrade>,
    onIdle?: () => void,
  ) {
    this.write = write;
    this.onIdle = onIdle;
  }
  subscribe = (listener: () => void) => {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  };
  getSnapshot = () => this.state;
  private patch(update: Partial<DraftSnapshot>) {
    this.state = { ...this.state, ...update };
    this.listeners.forEach((listener) => listener());
  }
  hasChanges = () => Object.values(this.state.cells).some(cellChanged);
  hasInvalid = () =>
    Object.values(this.state.cells).some((cell) => Boolean(cell.error));
  setFrozen = (frozen: boolean) => this.patch({ frozen });
  attach = () => {
    this.active = true;
  };
  detach = () => {
    this.active = false;
    this.pending.clear();
  };

  receive(data: GradeGrid) {
    const old = this.state.data;
    if (
      old &&
      signature(old) !== signature(data) &&
      (this.hasChanges() || this.state.saving)
    ) {
      this.pending.clear();
      this.patch({
        paused: true,
        warning:
          "Roster atau konfigurasi komponen berubah. Muat ulang sebelum melanjutkan.",
      });
      return;
    }
    // A background GET started before the current PUT must not undo its acknowledgement.
    if (this.state.saving || this.state.paused) return;
    const cells: Record<string, DraftCell> = {};
    let overwrittenFinalized = false;
    for (const row of data.grades)
      for (const component of data.components) {
        const key = cellKey(row.enrollment_id, component.id);
        const previous = this.state.cells[key];
        const value = String(row.scores[component.id] ?? "");
        const dirty =
          previous && canonical(previous.value) !== canonical(previous.saved);
        if (dirty && row.status !== "finalized") cells[key] = previous;
        else {
          overwrittenFinalized ||= Boolean(dirty && row.status === "finalized");
          cells[key] = {
            value,
            saved: value,
            version: previous?.version ?? 0,
            error: null,
            failure: null,
          };
        }
      }
    this.patch({
      data,
      cells,
      ...(overwrittenFinalized
        ? {
            warning:
              "Nilai telah dirilis dari sesi lain. Perubahan lokal pada nilai final tidak disimpan.",
          }
        : {}),
    });
  }

  replace(data: GradeGrid) {
    if (this.state.saving) return;
    this.patch({
      data: null,
      cells: {},
      paused: false,
      error: null,
      warning: null,
    });
    this.receive(data);
  }

  discard() {
    if (this.state.saving) return;
    this.pending.clear();
    this.patch({
      cells: Object.fromEntries(
        Object.entries(this.state.cells).map(([key, cell]) => [
          key,
          { ...cell, value: cell.saved, error: null, failure: null },
        ]),
      ),
      error: null,
    });
  }

  edit(enrollment: string, componentId: string, value: string) {
    const row = this.state.data?.grades.find(
      (item) => item.enrollment_id === enrollment,
    );
    const component = this.state.data?.components.find(
      (item) => item.id === componentId,
    );
    const key = cellKey(enrollment, componentId);
    const cell = this.state.cells[key];
    if (
      !cell ||
      !component ||
      row?.status === "finalized" ||
      this.state.paused ||
      this.state.frozen
    )
      return;
    this.patch({
      error: null,
      cells: {
        ...this.state.cells,
        [key]: {
          ...cell,
          value,
          version: cell.version + 1,
          error: validateScore(value, component.max_score),
          failure: null,
        },
      },
    });
  }

  private changes(enrollment: string) {
    return this.state.data!.components.flatMap((component) => {
      const key = cellKey(enrollment, component.id);
      const cell = this.state.cells[key];
      return cell &&
        !cell.error &&
        !cell.failure &&
        canonical(cell.value) !== canonical(cell.saved)
        ? [{ key, component: component.id, cell }]
        : [];
    });
  }

  queue(enrollment: string): Promise<void> {
    if (
      !this.active ||
      this.state.paused ||
      !this.state.data ||
      !this.changes(enrollment).length
    )
      return this.work ?? Promise.resolve();
    this.pending.add(enrollment);
    if (!this.work) {
      this.patch({ saving: true });
      this.work = this.drain().finally(() => {
        this.work = null;
        this.patch({ saving: false });
        if (this.active) this.onIdle?.();
      });
    }
    return this.work;
  }

  private async drain() {
    while (this.active && this.pending.size && !this.state.paused) {
      const enrollment = this.pending.values().next().value!;
      this.pending.delete(enrollment);
      if (
        this.state.data!.grades.find((row) => row.enrollment_id === enrollment)
          ?.status === "finalized"
      )
        continue;
      const changes = this.changes(enrollment);
      if (!changes.length) continue;
      const payload: ScoreChanges = Object.fromEntries(
        changes.map(({ component, cell }) => [
          component,
          canonical(cell.value) || null,
        ]),
      );
      try {
        const result = await this.write(enrollment, payload);
        const cells = { ...this.state.cells };
        for (const { key, component } of changes) {
          cells[key] = {
            ...cells[key],
            saved: payload[component] ?? "",
            failure: null,
          };
        }
        const data = this.state.data!;
        this.patch({
          cells,
          data: {
            ...data,
            grades: data.grades.map((row) => {
              if (row.enrollment_id !== enrollment) return row;
              const scores = { ...row.scores };
              for (const [key, value] of Object.entries(payload)) {
                if (value === null) delete scores[key];
                else scores[key] = value;
              }
              return {
                ...row,
                scores,
                final_score: result.final_score,
                status: result.status,
              };
            }),
          },
        });
      } catch (error) {
        const message =
          error instanceof Error
            ? error.message
            : "Penyimpanan gagal. Coba Simpan semua.";
        const cells = { ...this.state.cells };
        for (const { key, cell } of changes)
          if (cells[key].version === cell.version)
            cells[key] = { ...cells[key], failure: message };
        this.pending.clear();
        this.patch({
          cells,
          error: message,
          paused:
            this.state.paused ||
            (error instanceof GradeSaveError &&
              [401, 403, 404].includes(error.status ?? 0)),
        });
      }
    }
  }

  async flush(): Promise<boolean> {
    if (this.work) await this.work;
    if (!this.active || this.state.paused || this.hasInvalid()) return false;
    this.patch({
      error: null,
      cells: Object.fromEntries(
        Object.entries(this.state.cells).map(([key, cell]) => [
          key,
          { ...cell, failure: null },
        ]),
      ),
    });
    while (this.active && this.hasChanges() && !this.state.paused) {
      for (const row of this.state.data!.grades)
        void this.queue(row.enrollment_id);
      if (this.work) await this.work;
      if (this.state.error || this.hasInvalid()) return false;
    }
    return this.active && !this.state.paused;
  }
}
