import { ArrowUpRight, BookOpen, CheckCheck, Clock3, Layers } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/useAuth";
import { CourseOverview } from "./CourseOverview";
import { useDashboard } from "./api";

const releaseDate = new Intl.DateTimeFormat("id-ID", { dateStyle: "medium", timeStyle: "short" });

function focusClassRow(classId: string) {
  const target = document.getElementById(`dashboard-class-${classId}`);
  target?.focus({ preventScroll: true });
  target?.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth", block: "center" });
}

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

  function openRelease(courseId: string, classId: string) {
    if (expandedCourse === courseId) {
      focusClassRow(classId);
    } else {
      focusClass.current = classId;
      setExpandedCourse(courseId);
    }
  }

  const admin = user?.role === "superadmin";
  const summaryCards = data ? [
    { label: "Mata Kuliah", value: data.course_count, icon: BookOpen, note: admin ? "Seluruh mata kuliah" : "Mata kuliah yang Anda ampu" },
    { label: "Jumlah Kelas", value: data.class_count, icon: Layers, note: "Di seluruh tahun akademik" },
    { label: "Belum Dirilis", value: data.pending_class_count, icon: Clock3, note: "Termasuk kelas kosong dan draft" },
  ] : [];

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
          <div className="mt-7 grid gap-4 sm:grid-cols-3">
            {summaryCards.map(({ label, value, icon: Icon, note }) => (
              <div className="rounded-xl border border-border bg-background p-5 sm:p-6" key={label}>
                <div className="flex items-center justify-between gap-3"><h2 className="text-sm font-medium text-muted-foreground">{label}</h2><Icon aria-hidden="true" className="size-4 text-muted-foreground" /></div>
                <p className="mt-4 text-3xl font-semibold tracking-tight tabular-nums">{value}</p>
                <p className="mt-2 text-xs leading-5 text-muted-foreground">{note}</p>
              </div>
            ))}
          </div>

          <div className="mt-9 grid items-start gap-8 xl:grid-cols-[minmax(0,1fr)_20rem]">
            <section aria-labelledby="courses-title" className="min-w-0">
              <div className="mb-4 flex items-center justify-between gap-3"><h2 className="text-base font-semibold" id="courses-title">{admin ? "Semua Mata Kuliah" : "Mata Kuliah Saya"}</h2><span className="text-xs text-muted-foreground">{data.course_count} mata kuliah</span></div>
              {data.courses.length === 0 ? (
                <div className="rounded-xl border border-dashed border-border bg-background px-6 py-10 text-center">
                  <BookOpen aria-hidden="true" className="mx-auto size-7 text-muted-foreground" />
                  <h3 className="mt-4 text-sm font-semibold">Belum ada mata kuliah</h3>
                  <p className="mx-auto mt-2 max-w-sm text-sm leading-6 text-muted-foreground">{admin ? "Mata kuliah dan kelas akan muncul di sini setelah ditambahkan." : "Mata kuliah akan muncul setelah Anda ditugaskan sebagai dosen pengampu kelas."}</p>
                </div>
              ) : <div className="space-y-3">{data.courses.map((course) => <CourseOverview course={course} expanded={expandedCourse === course.id} key={course.id} onToggle={() => setExpandedCourse(expandedCourse === course.id ? null : course.id)} />)}</div>}
            </section>

            <section aria-labelledby="releases-title" className="min-w-0">
              <h2 className="mb-4 text-base font-semibold" id="releases-title">Rilis Terbaru</h2>
              <div className="overflow-hidden rounded-xl border border-border bg-background">
                {data.recently_released.length === 0 ? (
                  <div className="p-6"><CheckCheck aria-hidden="true" className="size-6 text-muted-foreground" /><h3 className="mt-4 text-sm font-semibold">Belum ada nilai dirilis</h3><p className="mt-2 text-sm leading-6 text-muted-foreground">Kelas dengan seluruh nilai yang telah difinalisasi akan muncul di sini.</p></div>
                ) : <ul className="divide-y divide-border">{data.recently_released.map((release) => (
                  <li key={release.id}>
                    <button className="flex w-full items-start gap-3 p-5 text-left outline-none hover:bg-muted/40 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring" onClick={() => openRelease(release.course_id, release.id)} type="button">
                      <span className="min-w-0 flex-1"><span className="block break-words text-xs font-medium text-muted-foreground">{release.course_code}</span><span className="mt-1 block break-words text-sm font-semibold">{release.course_name}</span><span className="mt-1 block break-words text-xs text-muted-foreground">Kelas {release.section} · {release.academic_year}</span><span className="mt-3 block text-xs text-muted-foreground">{release.released_at ? <time dateTime={release.released_at}>{releaseDate.format(new Date(release.released_at))}</time> : "Waktu rilis tidak tersedia"}</span></span>
                      <ArrowUpRight aria-hidden="true" className="mt-1 size-4 shrink-0 text-muted-foreground" />
                    </button>
                  </li>
                ))}</ul>}
              </div>
            </section>
          </div>
        </>
      )}
    </section>
  );
}
