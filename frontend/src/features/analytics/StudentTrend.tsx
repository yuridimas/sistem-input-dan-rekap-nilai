/**
 * Visualisasi rata-rata semester dan kelas sumber pada halaman mahasiswa.
 * Transformasi buildStudentTrend menjaga titik chart dan tabel alternatif tetap konsisten.
 */
import {
  CartesianGrid,
  Line,
  LineChart,
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
import { buildStudentTrend, type GradeHistoryEntry, type SemesterTrend } from "./data";
import { AccessibleTable, ChartSection } from "./Charts";

/**
 * Sajikan kelas pembentuk rata-rata; payload belum aktif/tersedia menghasilkan null.
 */
function TrendTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: SemesterTrend }>;
}) {
  if (!active || !payload?.[0]) return null;
  const point = payload[0].payload;

  return (
    <div className="max-w-sm rounded-md border bg-background p-3 text-sm shadow-sm">
      <p className="font-medium">
        {point.semester}: {point.average.toFixed(2)} ({point.count} kelas)
      </p>
      <ul className="mt-2 space-y-1">
        {point.entries.map((entry, index) => (
          <li key={entry.grade_id ?? entry.enrollment_id ?? index}>
            {entry.course.code ?? entry.course.name ?? "Mata kuliah"} · Kelas{" "}
            {entry.class.section} · {entry.class.academic_year}:{" "}
            {Number(entry.final_score).toFixed(2)}
          </li>
        ))}
      </ul>
    </div>
  );
}

/**
 * Render tren hasil final atau pesan kosong dengan tabel alternatif yang dapat diakses.
 */
export function StudentTrend({ history }: { history: GradeHistoryEntry[] }) {
  const trend = buildStudentTrend(history);
  if (trend.length === 0) {
    return (
      <p
        className="rounded-md border px-4 py-8 text-center text-sm text-muted-foreground"
        role="status"
      >
        Belum ada riwayat nilai final untuk ditampilkan.
      </p>
    );
  }

  return (
    <ChartSection
      description={
        "Rata-rata sederhana dari seluruh nilai final pada kelas yang dapat Anda akses. " +
        "Arahkan atau fokuskan titik untuk melihat rincian kelas."
      }
      headingLevel="h2"
      title="Rata-rata nilai per semester"
    >
      <div
        aria-label="Grafik rata-rata nilai final per semester"
        className="h-72 w-full min-w-0"
        role="img"
      >
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={trend}
            margin={{ top: 16, right: 16, bottom: 8, left: -12 }}
          >
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="semester" tick={{ fontSize: 12 }} />
            <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
            <Tooltip content={<TrendTooltip />} />
            <Line
              activeDot={{ r: 7 }}
              dataKey="average"
              dot={{ r: 5 }}
              isAnimationActive={false}
              name="Rata-rata"
              stroke="#2563eb"
              strokeWidth={2}
              type="monotone"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <AccessibleTable label="Tabel rata-rata nilai per semester">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Semester</TableHead>
              <TableHead>Rata-rata</TableHead>
              <TableHead>Jumlah kelas</TableHead>
              <TableHead>Rincian nilai kelas</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {trend.map((point) => (
              <TableRow key={point.semester}>
                <TableCell>{point.semester}</TableCell>
                <TableCell>{point.average.toFixed(2)}</TableCell>
                <TableCell>{point.count}</TableCell>
                <TableCell>
                  {point.entries
                    .map((entry) => {
                      const courseName =
                        entry.course.code ?? entry.course.name ?? "Mata kuliah";
                      const score = Number(entry.final_score).toFixed(2);
                      return `${courseName} · Kelas ${entry.class.section} (${score})`;
                    })
                    .join("; ")}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </AccessibleTable>
    </ChartSection>
  );
}
