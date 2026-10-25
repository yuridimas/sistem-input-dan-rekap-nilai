import {
  Bar,
  BarChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { GradeGrid } from "@/features/grades/types";
import {
  buildClassAnalytics,
  distributionChartLabel,
  type AnalyticsMode,
} from "./data";
import { CATEGORY_COLORS, CATEGORY_LABELS } from "./chartTokens";
import {
  AccessibleTable,
  BreakdownLegend,
  ChartSection,
} from "./Charts";

export function ClassCharts({
  grid,
  mode,
}: {
  grid: GradeGrid;
  mode: AnalyticsMode;
}) {
  const analytics = buildClassAnalytics(grid, mode);
  const modeLabel = mode === "finalized" ? "nilai final" : "draft lengkap";

  if (analytics.analyzedCount === 0) {
    const emptyMessage =
      mode === "finalized"
        ? "Belum ada nilai final untuk dianalisis (0 mahasiswa dianalisis)."
        : [
            "Belum ada draft lengkap dengan semua skor valid (0 mahasiswa dianalisis).",
            `${analytics.excludedDraftCount} draft tidak lengkap atau tidak valid dikecualikan.`,
          ].join(" ");
    return (
      <p
        className="rounded-md border px-4 py-8 text-center text-sm text-muted-foreground"
        role="status"
      >
        {emptyMessage}
      </p>
    );
  }

  return (
    <div className="space-y-5">
      <p className="text-sm text-muted-foreground" role="status">
        Menganalisis {analytics.analyzedCount} mahasiswa dengan {modeLabel}.
        {mode === "draft" && analytics.excludedDraftCount > 0
          ? ` ${analytics.excludedDraftCount} draft belum lengkap atau tidak valid dikecualikan.`
          : ""}
      </p>
      <ChartSection
        description={`Jumlah mahasiswa pada setiap rentang ${modeLabel}; nilai diambil dari hasil tersimpan.`}
        title="Distribusi nilai kelas"
      >
        <div
          aria-label={distributionChartLabel(mode)}
          className="h-64 w-full min-w-0"
          role="img"
        >
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={analytics.distribution}
              margin={{ top: 12, right: 8, bottom: 4, left: -20 }}
            >
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="label" interval={0} tick={{ fontSize: 10 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12 }} width={40} />
              <Tooltip formatter={(value) => [`${value} mahasiswa`, "Jumlah"]} />
              <Bar
                dataKey="count"
                fill="#2563eb"
                name="Mahasiswa"
                radius={[3, 3, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <AccessibleTable label="Tabel distribusi nilai kelas">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Rentang nilai</TableHead>
                <TableHead>Jumlah mahasiswa</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {analytics.distribution.map((bucket) => (
                <TableRow key={bucket.label}>
                  <TableCell>{bucket.label}</TableCell>
                  <TableCell>{bucket.count}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </AccessibleTable>
      </ChartSection>

      <ChartSection
        description={
          "Kontribusi = skor ÷ nilai maksimum × bobot. Skala 0–100; " +
          "nilai final tersimpan ditampilkan terpisah."
        }
        title="Kontribusi komponen per mahasiswa"
      >
        {analytics.unavailableBreakdownCount > 0 && (
          <p className="mb-3 text-sm text-muted-foreground" role="status">
            Rincian tidak tersedia untuk{" "}
            {analytics.unavailableBreakdownCount} nilai lama yang memiliki
            skor komponen belum lengkap; nilai final tetap ditampilkan.
          </p>
        )}
        <div
          aria-label="Grafik kontribusi mahasiswa"
          className="max-h-[520px] overflow-y-auto rounded-md"
          role="region"
          tabIndex={0}
        >
          <div
            aria-label="Batang kontribusi Tugas, UTS, UAS, dan Kustom per mahasiswa"
            className="w-full min-w-0"
            role="img"
            style={{ height: Math.max(240, analytics.breakdown.length * 42) }}
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={analytics.breakdown}
                layout="vertical"
                margin={{ top: 8, right: 36, bottom: 8, left: 16 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis domain={[0, 100]} tick={{ fontSize: 12 }} type="number" />
                <YAxis
                  dataKey="nim"
                  tick={{ fontSize: 12 }}
                  type="category"
                  width={84}
                />
                <Tooltip
                  formatter={(value, name) => [
                    Number(value).toFixed(2),
                    CATEGORY_LABELS[
                      name as keyof typeof CATEGORY_LABELS
                    ] ?? String(name),
                  ]}
                />
                <ReferenceLine x={100} stroke="#737373" strokeDasharray="4 4" />
                {(["tugas", "uts", "uas", "custom"] as const).map(
                  (category) => (
                    <Bar
                      dataKey={category}
                      fill={CATEGORY_COLORS[category]}
                      isAnimationActive={false}
                      key={category}
                      name={category}
                      stackId="contribution"
                    />
                  ),
                )}
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <BreakdownLegend />
        <AccessibleTable label="Tabel kontribusi komponen per mahasiswa">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>NIM</TableHead>
                <TableHead>Nama</TableHead>
                <TableHead>Tugas</TableHead>
                <TableHead>UTS</TableHead>
                <TableHead>UAS</TableHead>
                <TableHead>Kustom</TableHead>
                <TableHead>Nilai final</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {analytics.breakdown.map((row) => (
                <TableRow key={row.studentId}>
                  <TableCell>{row.nim}</TableCell>
                  <TableCell>{row.studentName}</TableCell>
                  {(["tugas", "uts", "uas", "custom"] as const).map(
                    (category) => (
                      <TableCell key={category}>
                        {row[category] === null
                          ? "Tidak tersedia"
                          : row[category]!.toFixed(2)}
                      </TableCell>
                    ),
                  )}
                  <TableCell>{row.finalScore.toFixed(2)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </AccessibleTable>
      </ChartSection>
    </div>
  );
}
