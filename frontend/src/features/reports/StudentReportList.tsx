import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { GradeHistoryEntry } from "@/features/analytics/data";
import { ReportDownloadButton } from "./ReportDownloadButton";

export function StudentReportList({ history }: { history: GradeHistoryEntry[] }) {
  return (
    <section className="space-y-3" aria-labelledby="student-reports-title">
      <h2 className="text-lg font-semibold" id="student-reports-title">Riwayat nilai final</h2>
      {!history.length ? (
        <p className="rounded-md border px-4 py-6 text-center text-sm text-muted-foreground" role="status">
          Belum ada laporan nilai final untuk diunduh.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-xl border bg-background">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Semester</TableHead>
                <TableHead>Mata kuliah</TableHead>
                <TableHead>Kelas</TableHead>
                <TableHead>Nilai akhir</TableHead>
                <TableHead><span className="sr-only">Tindakan</span></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {history.map((entry) => (
                <TableRow key={entry.enrollment_id}>
                  <TableCell>{entry.course.semester}</TableCell>
                  <TableCell>{entry.course.code ?? entry.course.name ?? "Mata kuliah"}</TableCell>
                  <TableCell>{entry.class.section} · {entry.class.academic_year}</TableCell>
                  <TableCell>{Number(entry.final_score).toFixed(2)}</TableCell>
                  <TableCell>
                    <ReportDownloadButton
                      ariaLabel={`Unduh PDF nilai ${entry.course.code ?? entry.course.name ?? "mahasiswa"}, kelas ${entry.class.section} ${entry.class.academic_year}`}
                      filename="nilai-mahasiswa.pdf"
                      label="Unduh PDF"
                      path={`/reports/student/${entry.enrollment_id}/pdf`}
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </section>
  );
}
