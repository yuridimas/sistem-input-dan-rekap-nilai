/**
 * State draft untuk grid nilai; hook React memasok adapter HTTP dan berlangganan snapshot.
 * Antrean menahan perubahan lokal selama respons server dan konfigurasi kelas belum sinkron.
 */
import type { GradeGrid, SavedGrade, ScoreChanges } from "./types";

/**
 * Kunci sel stabil untuk pasangan UUID enrollment dan komponen pada snapshot.
 */
export const cellKey = (enrollment: string, component: string) =>
  `${enrollment}/${component}`;
// Angka nonnegatif dengan maksimal dua desimal; .5 dan 5. diterima, eksponen tidak.
const decimal = /^(?:\d+(?:\.\d{0,2})?|\.\d{1,2})$/;
/**
 * Terima pemisah desimal lokal tanpa mengubah nilai teks yang sedang diedit.
 */
const textNumber = (value: string) => value.trim().replace(",", ".");
/**
 * Bandingkan nilai numerik setara tanpa memaksa tampilan input pengguna berubah.
 * @returns Teks angka, string kosong untuk hapus, atau penanda invalid untuk teks tidak sah.
 */
const canonical = (value: string) => {
  const text = textNumber(value);
  return text === ""
    ? ""
    : decimal.test(text)
      ? String(Number(text))
      : `invalid:${value}`;
};

/**
 * Validasi input editor sebelum masuk antrean; string kosong berarti penghapusan skor.
 * @param value Teks input; maximum adalah batas komponen dalam bentuk string desimal.
 * @returns Pesan kesalahan, atau null jika kosong/valid; tidak mengirim request.
 */
export function validateScore(value: string, maximum: string): string | null {
  const text = textNumber(value);
  if (text === "") return null;
  if (!decimal.test(text)) return "Gunakan angka dengan maksimal dua desimal.";
  if (!Number.isFinite(Number(text)) || Number(text) > Number(maximum))
    return `Nilai harus antara 0 dan ${maximum}.`;
  return null;
}

/**
 * Pisahkan teks lokal, nilai terkonfirmasi, dan versi edit agar respons lama tetap aman.
 */
export interface DraftCell {
  value: string;
  saved: string;
  version: number;
  error: string | null;
  failure: string | null;
}
/**
 * Anggap format setara seperti 1 dan 1,00 sebagai nilai sama agar tidak menulis ulang.
 */
export const cellChanged = (cell: DraftCell) =>
  canonical(cell.value) !== canonical(cell.saved);
/**
 * Snapshot immutable yang dibaca React; paused menahan antrean hingga pemulihan.
 */
export interface DraftSnapshot {
  data: GradeGrid | null;
  cells: Record<string, DraftCell>;
  saving: boolean;
  frozen: boolean;
  paused: boolean;
  error: string | null;
  warning: string | null;
}
/**
 * Bawa status HTTP dari adapter agar engine dapat membedakan kegagalan akses.
 */
export class GradeSaveError extends Error {
  status: number | undefined;
  /**
   * Simpan pesan dan status opsional untuk kebijakan pause saat penyimpanan gagal.
   */
  constructor(message: string, status?: number) {
    super(message);
    this.status = status;
  }
}

/**
 * Deteksi perubahan struktur kelas tanpa menganggap perubahan skor sebagai konflik roster.
 */
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

/**
 * Kelola edit dan pengiriman per enrollment tanpa bergantung pada lifecycle React.
 * Adapter write menyimpan satu baris; onIdle memungkinkan hook memuat ulang hasil server.
 */
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

  /**
   * Terima adapter penyimpanan async dan callback opsional setelah antrean selesai.
   * Konstruksi hanya menyiapkan state; request dimulai lewat queue atau flush.
   */
  constructor(
    write: (row: string, payload: ScoreChanges) => Promise<SavedGrade>,
    onIdle?: () => void,
  ) {
    this.write = write;
    this.onIdle = onIdle;
  }
  /**
   * Daftarkan listener snapshot dan kembalikan cleanup untuk useSyncExternalStore.
   */
  subscribe = (listener: () => void) => {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  };
  /**
   * Pertahankan referensi snapshot sampai patch berikutnya agar subscription React stabil.
   */
  getSnapshot = () => this.state;
  /**
   * Ganti snapshot sebelum memberi tahu listener agar render membaca state terbaru.
   */
  private patch(update: Partial<DraftSnapshot>) {
    this.state = { ...this.state, ...update };
    this.listeners.forEach((listener) => listener());
  }
  /**
   * Periksa selisih lokal terhadap acknowledgement terakhir, termasuk penghapusan skor.
   */
  hasChanges = () => Object.values(this.state.cells).some(cellChanged);
  /**
   * Tahan flush/finalisasi bila salah satu input gagal validasi editor.
   */
  hasInvalid = () =>
    Object.values(this.state.cells).some((cell) => Boolean(cell.error));
  /**
   * Kunci edit selama persiapan finalisasi tanpa membatalkan pengiriman yang berjalan.
   */
  setFrozen = (frozen: boolean) => this.patch({ frozen });
  /**
   * Aktifkan lagi engine yang dipertahankan hook saat subscription dipasang ulang.
   */
  attach = () => {
    this.active = true;
  };
  /**
   * Hentikan pekerjaan berikutnya saat unmount; request yang terlanjur dikirim tetap berjalan.
   */
  detach = () => {
    this.active = false;
    this.pending.clear();
  };

  /**
   * Gabungkan GET terbaru sambil mempertahankan draft lokal yang masih boleh diedit.
   * Perubahan struktur saat ada edit menghentikan antrean sampai pengguna memuat ulang.
   */
  receive(data: GradeGrid) {
    const old = this.state.data;
    // Skor tidak boleh dipetakan ke roster/komponen baru ketika masih ada edit lokal.
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

  /**
   * Terima reload eksplisit dengan membuang draft lama setelah tidak ada save berjalan.
   */
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

  /**
   * Pulihkan teks terkonfirmasi tanpa request; ditolak selama save masih berlangsung.
   */
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

  /**
   * Ubah teks sel dan versi edit; abaikan sel final, engine paused, atau editor frozen.
   * @param value String input mentah; validasi disimpan di snapshot, bukan dilempar sebagai error.
   */
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

  /**
   * Pilih perubahan valid yang belum gagal untuk satu enrollment yang ada pada grid.
   */
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

  /**
   * Gabungkan permintaan save per enrollment ke satu drain agar PUT tidak saling mendahului.
   * @returns Promise antrean aktif; error penyimpanan dicatat pada snapshot.
   */
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

  /**
   * Kirim baris berurutan; acknowledgement memperbarui saved sambil menjaga teks edit terbaru.
   * Efek: memanggil adapter write serta memperbarui saved/error; antrean berhenti saat paused.
   */
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
        // Perbarui saved saja; teks yang diketik ketika PUT berjalan harus tetap dipertahankan.
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
          // Error request lama tidak boleh menandai edit yang dibuat sesudah request tersebut.
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

  /**
   * Coba ulang sel gagal dan tunggu seluruh perubahan valid sebelum finalisasi/navigasi.
   * @returns false jika ada input invalid, error save, paused, atau engine tidak aktif.
   */
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
