import { Link, useParams } from "react-router-dom";

import { PageHeader, QueryState } from "@/features/academic/Management";
import { useAcademicQuery, type Student } from "@/features/academic/api";
import { StudentTrend } from "./StudentTrend";
import type { GradeHistoryEntry } from "./data";
import { StudentReportList } from "@/features/reports/StudentReportList";

export function StudentDetailPage() {
  const { studentId } = useParams();
  const student = useAcademicQuery<Student>(
    `/students/${studentId}`,
    Boolean(studentId),
  );
  const history = useAcademicQuery<GradeHistoryEntry[]>(
    `/students/${studentId}/history`,
    Boolean(studentId) && Boolean(student.data) && !student.error,
  );

  if (student.isPending || student.error) return <QueryState query={student} />;

  return (
    <section className="mx-auto max-w-5xl space-y-5">
      <Link
        className="inline-flex h-7 items-center rounded-md border px-2.5 text-sm hover:bg-muted"
        to="/students"
      >
        Kembali ke mahasiswa
      </Link>
      <PageHeader
        description={`NIM ${student.data.nim} · ${student.data.email || "Email belum tersedia"}`}
        title={student.data.full_name}
      />
      {history.isPending || history.error ? (
        <QueryState query={history} />
      ) : (
        <>
          <StudentTrend history={history.data ?? []} />
          <StudentReportList history={history.data ?? []} />
          <p className="text-xs text-muted-foreground">
            Riwayat hanya mencakup nilai final dari kelas yang dapat diakses akun Anda.
          </p>
        </>
      )}
    </section>
  );
}
