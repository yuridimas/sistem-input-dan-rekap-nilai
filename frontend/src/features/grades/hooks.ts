/**
 * Koordinasi React Query dan GradeDraft untuk editor serta dialog finalisasi.
 * Hook menahan edit ketika menyiapkan rilis dan memulihkan status jika hasil request tidak pasti.
 */
import {
  useEffect,
  useMemo,
  useRef,
  useState,
  useSyncExternalStore,
} from "react";
import { useQueryClient } from "@tanstack/react-query";
import axios from "axios";

import api from "@/lib/api";
import { errorMessage, useAcademicQuery } from "@/features/academic/api";
import { useAuth } from "@/features/auth/useAuth";
import { GradeDraft, GradeSaveError } from "./draft";
import type {
  FinalizeResult,
  GradeGrid,
  MissingScore,
  SavedGrade,
} from "./types";

/**
 * Daftarkan sel tanpa entri skor untuk fokus/validasi dialog; nilai nol tetap dianggap
 * terisi.
 * @param data Snapshot grid server. @returns Daftar sel kosong, bisa kosong.
 */
export function missingCells(data: GradeGrid) {
  return data.grades.flatMap((row) =>
    data.components.flatMap((component) =>
      component.id in row.scores
        ? []
        : [
            {
              student_nim: row.student.nim,
              component_name: component.name,
              enrollment: row.enrollment_id,
              component: component.id,
            },
          ],
    ),
  );
}
/**
 * Cek kesiapan editor dengan bobot dalam satuan seperseratus persen.
 * @returns boolean; validasi ini membantu UI, keputusan final tetap dilakukan backend.
 */
export function configurationValid(data: GradeGrid) {
  return (
    data.components.length > 0 &&
    data.components.every(
      (row) => Number(row.weight) > 0 && Number(row.max_score) > 0,
    ) &&
    data.components.reduce(
      (sum, row) => sum + Math.round(Number(row.weight) * 100),
      0,
    // 100 persen dikali 100 menghindari perbandingan jumlah float desimal secara langsung.
    ) === 10000 &&
    data.components.some((row) => row.category === "uts") &&
    data.components.some((row) => row.category === "uas")
  );
}

/**
 * Hubungkan engine draft dengan snapshot server per pengguna dan kelas.
 * @param classId UUID kelas; enabled mengaktifkan query awal saat tab diperlukan.
 * @returns State/aksi editor; efek mencakup HTTP save/finalisasi dan invalidasi cache.
 */
export function useGradeEntry(classId: string, enabled: boolean) {
  const client = useQueryClient();
  const { user, hasTokens } = useAuth();
  const path = `/classes/${classId}/grades`;
  const engine = useMemo(() => {
    let refreshRevision = 0;
    const key = ["academic", user?.id, path];
    const draft = new GradeDraft(
      async (enrollment, payload) => {
        try {
          return (
            await api.put<SavedGrade>(
              `/enrollments/${enrollment}/scores`,
              payload,
            )
          ).data;
        } catch (error) {
          throw new GradeSaveError(
            errorMessage(error),
            axios.isAxiosError(error) ? error.response?.status : undefined,
          );
        }
      },
      () => {
        const revision = ++refreshRevision;
        void client
          .invalidateQueries(
            { queryKey: key, exact: true },
            { throwOnError: true },
          )
          .then(() => {
            // Deliver completed refreshes even when TanStack structural sharing reuses their identity.
            const data = client.getQueryData<GradeGrid>(key);
            if (data && revision === refreshRevision) draft.receive(data);
          })
          .catch(() => {
            /* The query error remains visible; preserve local drafts. */
          });
      },
    );
    return draft;
  }, [client, user?.id, path]);
  const snapshot = useSyncExternalStore(engine.subscribe, engine.getSnapshot);
  const query = useAcademicQuery<GradeGrid>(
    path,
    enabled || Boolean(snapshot.data),
  );
  const [dialogOpen, setDialogOpen] = useState(false);
  const [preparing, setPreparing] = useState(false);
  const [finalizing, setFinalizing] = useState(false);
  const [uncertain, setUncertain] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [serverMissing, setServerMissing] = useState<MissingScore[]>([]);
  const finalizeBusy = useRef(false);

  useEffect(() => {
    engine.attach();
    return engine.detach;
  }, [engine]);
  useEffect(() => {
    if (query.data) engine.receive(query.data);
  }, [engine, query.data]);

  /**
   * Refetch snapshot dan kirimkan ke engine sebelum keputusan finalisasi.
   * @returns Promise grid; melempar error query atau error ketika data belum tersedia.
   */
  async function fresh() {
    const result = await query.refetch({ throwOnError: true });
    if (!result.data) throw new Error("Data nilai belum tersedia.");
    engine.receive(result.data);
    return result.data;
  }
  /**
   * Segarkan grid/ranking/history dan dashboard setelah status rilis berubah.
   * @returns Promise seluruh invalidasi; tidak menulis langsung data server.
   */
  async function invalidate() {
    await Promise.all([
      client.invalidateQueries({ queryKey: ["academic", user?.id] }),
      client.invalidateQueries({
        queryKey: ["dashboard", "summary", user?.id],
      }),
    ]);
  }
  /**
   * Buang draft lokal lewat reload eksplisit ketika tidak ada save yang sedang berjalan.
   * @returns boolean sukses; kegagalan dicatat pada actionError.
   */
  async function reload() {
    if (engine.getSnapshot().saving) return false;
    try {
      engine.replace(await fresh());
      setActionError(null);
      return true;
    } catch (error) {
      setActionError(errorMessage(error));
      return false;
    }
  }
  /**
   * Bekukan edit dan tunggu flush sebelum membuka konfirmasi rilis.
   * Jika validasi gagal, tampilkan error dan buka kembali editor; tidak memanggil finalize.
   */
  async function prepare() {
    if (engine.getSnapshot().frozen || engine.getSnapshot().paused) return;
    engine.setFrozen(true);
    setPreparing(true);
    setActionError(null);
    setServerMissing([]);
    try {
      if (!(await engine.flush()))
        throw new Error(
          "Selesaikan kesalahan input atau penyimpanan sebelum finalisasi.",
        );
      const data = await fresh();
      if (engine.getSnapshot().paused)
        throw new Error(
          "Konfigurasi kelas berubah. Muat ulang terlebih dahulu.",
        );
      if (!configurationValid(data) || !data.grades.length)
        throw new Error(
          "Lengkapi roster dan konfigurasi komponen sebelum finalisasi.",
        );
      if (data.grades.some((row) => row.status === "finalized"))
        throw new Error(
          "Kelas sudah memiliki nilai final; finalisasi ulang tidak tersedia.",
        );
      setDialogOpen(true);
    } catch (error) {
      setActionError(
        error instanceof Error ? error.message : errorMessage(error),
      );
      engine.setFrozen(false);
    } finally {
      setPreparing(false);
    }
  }
  /**
   * Buka kembali editor ketika konfirmasi dibatalkan; abaikan selama finalisasi berjalan.
   */
  function closeDialog() {
    if (finalizeBusy.current) return;
    setDialogOpen(false);
    engine.setFrozen(false);
    setServerMissing([]);
    setActionError(null);
  }
  /**
   * Periksa snapshot terbaru sebelum POST agar rilis paralel tidak dipicu ulang.
   * Error tanpa kepastian hasil mempertahankan lock UI sampai status server diperiksa.
   */
  async function confirm() {
    if (finalizeBusy.current || !dialogOpen) return;
    finalizeBusy.current = true;
    setFinalizing(true);
    setActionError(null);
    try {
      const data = await fresh();
      if (data.grades.some((row) => row.status === "finalized")) {
        setDialogOpen(false);
        engine.setFrozen(false);
        setNotice(
          "Kelas sudah memiliki nilai final. Status terbaru telah dimuat.",
        );
        await invalidate();
        return;
      }
      if (
        missingCells(data).length ||
        !configurationValid(data) ||
        engine.hasChanges()
      )
        return;
      const { data: result } = await api.post<FinalizeResult>(
        `/classes/${classId}/finalize`,
      );
      setNotice(
        `${result.finalized_count} mahasiswa berhasil dirilis. ${result.notified} notifikasi diantrekan; ini bukan konfirmasi email telah diterima.`,
      );
      setDialogOpen(false);
      await invalidate();
      engine.setFrozen(false);
    } catch (error) {
      const status = axios.isAxiosError(error)
        ? error.response?.status
        : undefined;
      const detail = axios.isAxiosError(error)
        ? error.response?.data?.detail
        : undefined;
      if (status === 422 && Array.isArray(detail?.missing)) {
        setServerMissing(detail.missing);
        setActionError(detail.message);
        try {
          await fresh();
        } catch {
          /* Retain the server's missing-score response. */
        }
      // Timeout/5xx tidak membuktikan rollback; periksa hasil rilis sebelum menawarkan retry.
      } else if (!status || status >= 500) {
        setUncertain(true);
        setDialogOpen(false);
        setActionError(
          "Hasil finalisasi belum dapat dipastikan. Periksa status server sebelum mencoba lagi.",
        );
      } else {
        setActionError(errorMessage(error));
        await invalidate();
        setDialogOpen(false);
        engine.setFrozen(false);
      }
    } finally {
      finalizeBusy.current = false;
      setFinalizing(false);
    }
  }
  /**
   * Rekonsiliasi hasil rilis yang tidak pasti melalui GET sebelum mengizinkan percobaan
   * lain.
   * Menyegarkan cache dan state UI; kegagalan tetap tampil sebagai actionError.
   */
  async function checkRelease() {
    setPreparing(true);
    try {
      const data = await fresh();
      setNotice(
        data.grades.length &&
          data.grades.every((row) => row.status === "finalized")
          ? "Seluruh nilai kelas sudah dirilis. Status terbaru telah dimuat."
          : "Status terbaru telah dimuat. Periksa nilai sebelum mencoba finalisasi kembali.",
      );
      setUncertain(false);
      setActionError(null);
      engine.setFrozen(false);
      await invalidate();
    } catch (error) {
      setActionError(errorMessage(error));
    } finally {
      setPreparing(false);
    }
  }
  return {
    engine,
    snapshot,
    query,
    hasTokens,
    dialogOpen,
    preparing,
    finalizing,
    uncertain,
    notice,
    actionError,
    serverMissing,
    prepare,
    confirm,
    closeDialog,
    checkRelease,
    reload,
    classId,
  };
}

/**
 * Kontrak state/aksi hook yang dibagikan grid dan guard navigasi.
 */
export type GradeEntry = ReturnType<typeof useGradeEntry>;
