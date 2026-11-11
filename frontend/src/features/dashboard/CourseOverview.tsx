/**
 * Kelompok mata kuliah yang dapat dibuka pada DashboardPage.
 * Props expanded/onToggle dikendalikan parent untuk satu pilihan ekspansi aktif.
 */
import { ChevronDown, GraduationCap } from "lucide-react";
import { Link } from "react-router-dom";

import type { DashboardCourse } from "./api";

/**
 * Sajikan kelas dan status rilis dari summary tanpa query tambahan per mata kuliah.
 */
export function CourseOverview({ course, expanded, onToggle }: {
  course: DashboardCourse;
  expanded: boolean;
  onToggle: () => void;
}) {
  const buttonId = `course-toggle-${course.id}`;
  const panelId = `course-classes-${course.id}`;

  return (
    <article className="overflow-hidden rounded-xl border border-border bg-background">
      <h3>
        <button
          aria-controls={panelId}
          aria-expanded={expanded}
          className="flex w-full items-center gap-4 p-4 text-left outline-none hover:bg-muted/40 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring sm:p-5"
          id={buttonId}
          onClick={onToggle}
          type="button"
        >
          <span aria-hidden="true" className="hidden size-11 shrink-0 place-items-center rounded-lg bg-muted text-muted-foreground sm:grid"><GraduationCap className="size-5" /></span>
          <span className="min-w-0 flex-1">
            <span className="block break-words text-xs font-medium text-muted-foreground">{course.code} · Semester {course.semester}</span>
            <span className="mt-1 block break-words text-sm font-semibold">{course.name}</span>
          </span>
          <span className="shrink-0 text-xs text-muted-foreground">{course.classes.length < course.class_count ? `5 kelas terbaru dari ${course.class_count}` : `${course.class_count} kelas`}</span>
          <ChevronDown aria-hidden="true" className={`size-4 shrink-0 text-muted-foreground transition-transform ${expanded ? "rotate-180" : ""}`} />
        </button>
      </h3>
      <div aria-labelledby={buttonId} hidden={!expanded} id={panelId} role="region">
        <div className="border-t border-border px-5 py-3 text-sm"><Link className="font-medium underline underline-offset-4" to={`/courses/${course.id}`}>Buka mata kuliah</Link></div>
        {course.classes.length === 0 ? (
          <p className="border-t border-border px-5 py-5 text-sm text-muted-foreground">Belum ada kelas untuk mata kuliah ini.</p>
        ) : (
          <ul className="border-t border-border bg-muted/20 px-4 sm:px-5">
            {course.classes.map((class_) => (
              <li className="flex flex-wrap items-center justify-between gap-3 border-b border-border py-4 outline-none last:border-0 focus-visible:rounded-lg focus-visible:ring-2 focus-visible:ring-ring" id={`dashboard-class-${class_.id}`} key={class_.id} tabIndex={-1}>
                <div className="min-w-0">
                  <p className="break-words text-sm font-medium"><Link className="underline-offset-4 hover:underline" to={`/classes/${class_.id}`}>Kelas {class_.section}</Link></p>
                  <p className="mt-1 break-words text-xs text-muted-foreground">{class_.academic_year} · {class_.student_count} mahasiswa</p>
                </div>
                <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${class_.status === "released" ? "bg-emerald-50 text-emerald-800" : "bg-amber-50 text-amber-900"}`}>
                  {class_.status === "released" ? "Sudah dirilis" : "Belum dirilis"}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </article>
  );
}
