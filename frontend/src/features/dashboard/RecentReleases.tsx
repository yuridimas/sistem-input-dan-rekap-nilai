import { ArrowUpRight, CheckCheck } from "lucide-react";

import type { DashboardRelease } from "./api";

const releaseDate = new Intl.DateTimeFormat("id-ID", { dateStyle: "medium", timeStyle: "short" });

/** Daftar rilis terbaru; parent menangani navigasi fokus ke kelas yang dipilih. */
export function RecentReleases({
  releases,
  onSelect,
}: {
  releases: DashboardRelease[];
  onSelect: (courseId: string, classId: string) => void;
}) {
  return (
    <section aria-labelledby="releases-title" className="min-w-0">
      <h2 className="mb-4 text-base font-semibold" id="releases-title">Rilis Terbaru</h2>
      <div className="overflow-hidden rounded-xl border border-border bg-background">
        {releases.length === 0 ? (
          <div className="p-6"><CheckCheck aria-hidden="true" className="size-6 text-muted-foreground" /><h3 className="mt-4 text-sm font-semibold">Belum ada nilai dirilis</h3><p className="mt-2 text-sm leading-6 text-muted-foreground">Kelas dengan seluruh nilai yang telah difinalisasi akan muncul di sini.</p></div>
        ) : <ul className="divide-y divide-border">{releases.map((release) => (
          <li key={release.id}>
            <button className="flex w-full items-start gap-3 p-5 text-left outline-none hover:bg-muted/40 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring" onClick={() => onSelect(release.course_id, release.id)} type="button">
              <span className="min-w-0 flex-1"><span className="block break-words text-xs font-medium text-muted-foreground">{release.course_code}</span><span className="mt-1 block break-words text-sm font-semibold">{release.course_name}</span><span className="mt-1 block break-words text-xs text-muted-foreground">Kelas {release.section} · {release.academic_year}</span><span className="mt-3 block text-xs text-muted-foreground">{release.released_at ? <time dateTime={release.released_at}>{releaseDate.format(new Date(release.released_at))}</time> : "Waktu rilis tidak tersedia"}</span></span>
              <ArrowUpRight aria-hidden="true" className="mt-1 size-4 shrink-0 text-muted-foreground" />
            </button>
          </li>
        ))}</ul>}
      </div>
    </section>
  );
}
