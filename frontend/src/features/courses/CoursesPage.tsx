/**
 * Daftar mata kuliah terotorisasi beserta pencarian lokal dan dialog pengelolaan.
 * Data berasal dari query akademik per pengguna; backend menentukan cakupan daftar.
 */
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Eye, Pencil, Plus, RefreshCw, Trash2 } from "lucide-react";
import type { ColumnDef } from "@tanstack/react-table";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { DataTable } from "@/components/data-table";
import {
  PageHeader,
  QueryState,
} from "@/features/academic/Management";
import { useAcademicQuery, type Course } from "@/features/academic/api";
import { useAuth } from "@/features/auth/useAuth";
import { CourseDialog } from "./CourseDialog";

/**
 * Kelola pencarian dan modal tanpa mencampurkan filter lokal ke kontrak API daftar.
 */
export function CoursesPage() {
  const { user } = useAuth();
  const query = useAcademicQuery<Course[]>("/courses");
  const [search, setSearch] = useState("");
  const [dialog, setDialog] = useState<{
    course?: Course;
    deleting?: boolean;
  } | null>(null);
  const rows =
    query.data?.filter((row) =>
      `${row.code} ${row.name}`.toLowerCase().includes(search.toLowerCase()),
    ) ?? [];
  const columns = useMemo<ColumnDef<Course>[]>(() => [
    {
      id: "course",
      size: 54,
      accessorFn: (course) => `${course.name} ${course.code}`,
      header: "Mata kuliah",
      cell: ({ row }) => (
        <div className="min-w-0 whitespace-normal text-wrap break-words">
          <span className="font-medium">
            {row.original.name}
          </span>
          <p className="mt-1 text-xs text-muted-foreground">{row.original.code}</p>
        </div>
      ),
    },
    {
      id: "semester",
      size: 24,
      accessorFn: (course) => `${course.semester} ${course.credits}`,
      header: "Semester / SKS",
      cell: ({ row }) => `${row.original.semester} · ${row.original.credits} SKS`,
    },
    {
      id: "actions",
      size: 22,
      header: "Tindakan",
      enableSorting: false,
      cell: ({ row }) => (
        <div className="flex justify-end gap-2">
          <Button aria-label={`Lihat mata kuliah ${row.original.name}`} render={<Link to={`/courses/${row.original.id}`} />} size="icon" variant="outline">
            <Eye aria-hidden="true" className="size-4" />
          </Button>
          {(user?.role === "superadmin" || row.original.created_by === user?.id) && (
            <>
              <Button aria-label={`Edit ${row.original.name}`} className="border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100 hover:text-blue-800 dark:border-blue-900 dark:bg-blue-950/50 dark:text-blue-300 dark:hover:bg-blue-900/60" onClick={() => setDialog({ course: row.original })} size="icon" variant="outline"><Pencil aria-hidden="true" className="size-4" /></Button>
              <Button aria-label={`Hapus ${row.original.name}`} onClick={() => setDialog({ course: row.original, deleting: true })} size="icon" variant="destructive"><Trash2 aria-hidden="true" className="size-4" /></Button>
            </>
          )}
        </div>
      ),
    },
  ], [user?.id, user?.role]);
  return (
    <section className="mx-auto max-w-6xl">
      <PageHeader
        description="Kelola identitas mata kuliah dan buka daftar kelasnya."
        title={
          user?.role === "superadmin" ? "Semua Mata Kuliah" : "Mata Kuliah Saya"
        }
      >
        <Button onClick={() => setDialog({})}>
          <Plus data-icon="inline-start" />
          Tambah mata kuliah
        </Button>
      </PageHeader>
      {query.error && <QueryState query={query} />}
      <DataTable
          actions={<Button aria-label="Segarkan" disabled={query.isFetching} onClick={() => void query.refetch()} type="button" variant="outline"><RefreshCw aria-hidden="true" className="size-4" /><span className="hidden sm:inline">Segarkan</span></Button>}
          columns={columns}
          data={rows}
          emptyMessage={query.isPending ? "Memuat data" : search ? "Tidak ada mata kuliah yang cocok dengan pencarian." : "Belum ada mata kuliah"}
          getRowId={(course) => course.id}
          search={<label className="flex items-center gap-2 whitespace-nowrap text-sm" htmlFor="course-search">Cari<Input className="w-48 sm:w-64" id="course-search" onChange={(event) => setSearch(event.target.value)} placeholder="Kode atau nama mata kuliah" type="search" value={search} /></label>}
        />
      {dialog && <CourseDialog {...dialog} close={() => setDialog(null)} />}
    </section>
  );
}
