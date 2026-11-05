import { BookOpen, Clock3, Layers } from "lucide-react";

import type { DashboardSummary } from "./api";

/** Kartu hitungan utama dashboard dengan catatan yang disesuaikan menurut peran. */
export function SummaryCards({ data, admin }: { data: DashboardSummary; admin: boolean }) {
  const cards = [
    { label: "Mata Kuliah", value: data.course_count, icon: BookOpen, note: admin ? "Seluruh mata kuliah" : "Mata kuliah yang Anda ampu" },
    { label: "Jumlah Kelas", value: data.class_count, icon: Layers, note: "Di seluruh tahun akademik" },
    { label: "Belum Dirilis", value: data.pending_class_count, icon: Clock3, note: "Termasuk kelas kosong dan draft" },
  ];

  return (
    <div className="mt-7 grid gap-4 sm:grid-cols-3">
      {cards.map(({ label, value, icon: Icon, note }) => (
        <div className="rounded-xl border border-border bg-background p-5 sm:p-6" key={label}>
          <div className="flex items-center justify-between gap-3"><h2 className="text-sm font-medium text-muted-foreground">{label}</h2><Icon aria-hidden="true" className="size-4 text-muted-foreground" /></div>
          <p className="mt-4 text-3xl font-semibold tracking-tight tabular-nums">{value}</p>
          <p className="mt-2 text-xs leading-5 text-muted-foreground">{note}</p>
        </div>
      ))}
    </div>
  );
}
