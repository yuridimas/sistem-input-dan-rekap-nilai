/**
 * Pemilihan populasi analytics pada tab kelas menggunakan snapshot server tersimpan.
 * Perubahan draft lokal yang belum tersimpan tidak dimasukkan ke grafik.
 */
import { useState } from "react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select";
import { NoData, QueryState } from "@/features/academic/Management";
import type { GradeGrid } from "@/features/grades/types";
import { useAcademicQuery } from "@/features/academic/api";
import { ClassCharts } from "./ClassCharts";
import type { AnalyticsMode } from "./data";

/**
 * Muat grid, pilih mode final/draft lengkap, dan ungkapkan jika ada perubahan lokal
 * tertunda.
 */
export function ClassAnalyticsPanel({
  classId,
  hasUnsavedChanges = false,
}: {
  classId: string;
  hasUnsavedChanges?: boolean;
}) {
  const [mode, setMode] = useState<AnalyticsMode>("finalized");
  const query = useAcademicQuery<GradeGrid>(`/classes/${classId}/grades`);

  if (query.isPending || query.error) return <QueryState query={query} />;
  if (!query.data?.grades.length) {
    return (
      <NoData description="Tambahkan mahasiswa ke roster untuk mulai melihat analisis kelas." />
    );
  }

  return (
    <section className="space-y-5" aria-labelledby="class-analytics-title">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="font-semibold" id="class-analytics-title">
            Analisis performa kelas
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Pilih satu status data agar grafik tidak mencampur nilai final dan
            draft.
          </p>
        </div>
        <label
          className="flex flex-col gap-1 text-sm font-medium"
          htmlFor="analytics-mode"
        >
          Data grafik
          <NativeSelect
            id="analytics-mode"
            onChange={(event) => setMode(event.target.value as AnalyticsMode)}
            value={mode}
          >
            <NativeSelectOption value="finalized">Nilai final</NativeSelectOption>
            <NativeSelectOption value="draft">Draft lengkap</NativeSelectOption>
          </NativeSelect>
        </label>
      </div>
      {hasUnsavedChanges && (
        <Alert>
          <AlertTitle>Grafik memakai data tersimpan</AlertTitle>
          <AlertDescription>
            Perubahan nilai lokal yang belum tersimpan belum ditampilkan dalam
            analisis ini.
          </AlertDescription>
        </Alert>
      )}
      {query.data.components.length === 0 ? (
        <NoData description="Tambahkan komponen penilaian sebelum melihat kontribusi dan distribusi nilai." />
      ) : (
        <ClassCharts grid={query.data} mode={mode} />
      )}
    </section>
  );
}
