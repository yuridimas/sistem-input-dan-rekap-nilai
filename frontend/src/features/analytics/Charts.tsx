/**
 * Wadah chart, tabel alternatif, dan legenda bersama untuk analytics.
 * Tabel menyediakan data yang sama tanpa bergantung pada kemampuan membaca visual grafik.
 */
import type { ReactNode } from "react";

import { CATEGORY_COLORS, CATEGORY_LABELS } from "./chartTokens";

/**
 * Pilih level heading sesuai hierarki parent dan beri nama area chart untuk aksesibilitas.
 */
export function ChartSection({
  title,
  description,
  children,
  headingLevel = "h3",
}: {
  title: string;
  description: string;
  children: ReactNode;
  headingLevel?: "h2" | "h3";
}) {
  const Heading = headingLevel;
  return (
    <section
      aria-label={title}
      className="min-w-0 rounded-lg border bg-background p-4 sm:p-5"
    >
      <Heading className="font-semibold">{title}</Heading>
      <p className="mt-1 text-sm text-muted-foreground">{description}</p>
      <div className="mt-4 min-w-0">{children}</div>
    </section>
  );
}

/**
 * Sediakan rincian data dalam region yang dapat difokuskan dan digulir lewat keyboard.
 */
export function AccessibleTable({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <details className="mt-3 text-sm">
      <summary className="w-fit cursor-pointer font-medium underline underline-offset-4">
        Lihat tabel data
      </summary>
      <div
        aria-label={label}
        className="mt-3 max-h-72 overflow-auto rounded-md border"
        role="region"
        tabIndex={0}
      >
        {children}
      </div>
    </details>
  );
}

/**
 * Pasangkan label teks dengan warna kategori sehingga informasi tidak bergantung warna
 * saja.
 */
export function BreakdownLegend() {
  return (
    <ul
      aria-label="Kategori kontribusi"
      className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-sm"
    >
      {(["tugas", "uts", "uas", "custom"] as const).map((category) => (
        <li className="flex items-center gap-2" key={category}>
          <span
            aria-hidden="true"
            className="size-3 rounded-sm"
            style={{ backgroundColor: CATEGORY_COLORS[category] }}
          />
          {CATEGORY_LABELS[category]}
        </li>
      ))}
    </ul>
  );
}
