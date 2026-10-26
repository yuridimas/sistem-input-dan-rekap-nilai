/**
 * Tampilan sementara route yang belum memiliki implementasi fitur.
 * Saat ini dipakai App untuk halaman pengguna administratif.
 */
import { ArrowUpRight, BookOpenCheck } from "lucide-react";

/**
 * Tampilkan status kesiapan halaman dari title; opsi dashboard mendukung tampilan
 * sambutan.
 */
export function PlaceholderPage({ title, dashboard = false }: { title: string; dashboard?: boolean }) {
  return (
    <section aria-labelledby="page-title" className="mx-auto max-w-5xl">
      <p className="text-sm font-medium text-muted-foreground">Ruang akademik</p>
      <h1 className="mt-1 text-2xl font-semibold tracking-tight" id="page-title">{title}</h1>
      <div className="mt-8 overflow-hidden rounded-2xl border border-border bg-background">
        <div className="grid gap-8 p-6 sm:grid-cols-[minmax(0,1fr)_16rem] sm:items-center sm:p-9">
          <div className="max-w-xl">
            <span className="grid size-11 place-items-center rounded-xl bg-primary/8 text-primary"><BookOpenCheck className="size-5" aria-hidden="true" /></span>
            <h2 className="mt-5 text-lg font-semibold">{dashboard ? "Selamat datang di ruang kerja Anda" : `${title} sedang disiapkan`}</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">{dashboard ? "Ringkasan kelas dan aktivitas akademik akan tersedia di sini." : "Halaman ini akan tersedia pada tahapan pengembangan berikutnya."}</p>
            {dashboard && <p className="mt-5 inline-flex items-center gap-2 text-sm font-medium text-muted-foreground">Fitur berikutnya sedang disiapkan <ArrowUpRight className="size-4" aria-hidden="true" /></p>}
          </div>
          <div aria-hidden="true" className="hidden rounded-xl border border-border bg-muted/30 p-4 sm:block">
            <div className="flex items-center gap-3 border-b border-border pb-4"><span className="grid size-9 place-items-center rounded-lg bg-background text-primary"><BookOpenCheck className="size-4" /></span><div className="flex-1"><div className="h-2.5 w-24 rounded bg-foreground/15" /><div className="mt-2 h-2 w-16 rounded bg-foreground/10" /></div></div>
            {["w-4/5", "w-3/5", "w-2/3"].map((width) => <div className="mt-4 flex items-center gap-3" key={width}><span className="size-8 rounded-full bg-primary/10" /><div className="flex-1"><div className={`h-2 rounded bg-foreground/15 ${width}`} /><div className="mt-2 h-1.5 w-1/2 rounded bg-foreground/10" /></div><span className="h-5 w-10 rounded-md bg-emerald-500/10" /></div>)}
          </div>
        </div>
      </div>
    </section>
  );
}
