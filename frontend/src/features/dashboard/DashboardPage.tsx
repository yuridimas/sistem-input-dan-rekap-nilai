/**
 * Ringkasan akademik dan rilis terbaru bagi admin maupun dosen.
 * Memakai satu query summary dan membuka baris kelas dari tindakan rilis terbaru.
 */
import { BookOpen } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/useAuth";
import { CourseOverview } from "./CourseOverview";
import { useDashboard } from "./api";
import { RecentReleases } from "./RecentReleases";
import { SummaryCards } from "./SummaryCards";

/**
 * Fokus/gulir baris kelas dengan menghormati prefers-reduced-motion pengguna.
 */
function focusClassRow(classId: string) {
  const target = document.getElementById(`dashboard-class-${classId}`);
  target?.focus({ preventScroll: true });
  target?.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth", block: "center" });
}

/**
 * Sajikan ringkasan role pengguna serta state loading/error dan ekspansi mata kuliah.
 */
export function DashboardPage() {
  const { user } = useAuth();
  const { data, isPending, isError, isFetching, refetch } = useDashboard(user?.id);
  const [expandedCourse, setExpandedCourse] = useState<string | null>(null);
  const focusClass = useRef<string | null>(null);

  useEffect(() => {
    if (focusClass.current) {
      focusClassRow(focusClass.current);
      focusClass.current = null;
    }
  }, [expandedCourse]);

  /**
   * Buka kelompok mata kuliah sebelum memfokuskan kelas jika barisnya belum terpasang.
   */
  function openRelease(courseId: string, classId: string) {
    if (expandedCourse === courseId) {
      focusClassRow(classId);
    } else {
      focusClass.current = classId;
      setExpandedCourse(courseId);
    }
  }

  const admin = user?.role === "superadmin";
  return (
    <section aria-labelledby="dashboard-title" className="mx-auto max-w-6xl">
      <p className="text-sm font-medium text-muted-foreground">Ruang akademik</p>
      <h1 className="mt-1 text-2xl font-semibold tracking-tight" id="dashboard-title">Dashboard</h1>
      <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">{admin ? "Pantau seluruh mata kuliah, kelas, dan perkembangan rilis nilai." : "Pantau kelas yang Anda ampu dan perkembangan rilis nilainya."}</p>

      {isPending ? (
        <div className="mt-8 rounded-xl border border-border bg-background p-8 text-sm text-muted-foreground" role="status">Memuat ringkasan akademik…</div>
      ) : isError ? (
        <div className="mt-8 rounded-xl border border-border bg-background p-6" role="alert">
          <h2 className="font-semibold">Ringkasan belum dapat dimuat</h2>
          <p className="mt-2 text-sm text-muted-foreground">Periksa koneksi Anda, lalu coba lagi.</p>
          <Button className="mt-4" disabled={isFetching} onClick={() => void refetch()} variant="outline">{isFetching ? "Memuat…" : "Coba lagi"}</Button>
        </div>
      ) : data && (
        <>
          <SummaryCards admin={admin} data={data} />

          <div className="mt-9 grid items-start gap-8 xl:grid-cols-[minmax(0,1fr)_20rem]">
            <section aria-labelledby="courses-title" className="min-w-0">
              <div className="mb-4 flex items-center justify-between gap-3"><h2 className="text-base font-semibold" id="courses-title">{admin ? "Semua Mata Kuliah" : "Mata Kuliah Saya"}</h2><span className="text-xs text-muted-foreground">{data.course_count} mata kuliah</span></div>
              {data.courses.length === 0 ? (
                <div className="rounded-xl border border-dashed border-border bg-background px-6 py-10 text-center">
                  <BookOpen aria-hidden="true" className="mx-auto size-7 text-muted-foreground" />
                  <h3 className="mt-4 text-sm font-semibold">Belum ada mata kuliah</h3>
                  <p className="mx-auto mt-2 max-w-sm text-sm leading-6 text-muted-foreground">{admin ? "Mata kuliah dan kelas akan muncul di sini setelah ditambahkan." : "Mata kuliah akan muncul setelah Anda ditugaskan sebagai dosen pengampu kelas."}</p>
                </div>
              ) : (
                <>
                  {data.course_count > 5 && <div className="mb-3 flex justify-end"><Link className="text-sm font-medium text-primary underline-offset-4 hover:underline" to="/courses">Lihat semua</Link></div>}
                  <div className="space-y-3">{data.courses.slice(0, 5).map((course) => <CourseOverview course={course} expanded={expandedCourse === course.id} key={course.id} onToggle={() => setExpandedCourse(expandedCourse === course.id ? null : course.id)} />)}</div>
                </>
              )}
            </section>

            <RecentReleases onSelect={openRelease} releases={data.recently_released} />
          </div>
        </>
      )}
    </section>
  );
}
