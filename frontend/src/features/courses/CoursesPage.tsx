/**
 * Daftar mata kuliah terotorisasi beserta pencarian lokal dan dialog pengelolaan.
 * Data berasal dari query akademik per pengguna; backend menentukan cakupan daftar.
 */
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Plus } from "lucide-react";
import type { ColumnDef } from "@tanstack/react-table";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { DataTable, DataTableToolbar } from "@/components/data-table";
import {
  NoData,
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
      accessorFn: (course) => `${course.name} ${course.code}`,
      header: "Mata kuliah",
      cell: ({ row }) => (
        <div className="max-w-72 whitespace-normal">
          <Link className="font-medium underline-offset-4 hover:underline" to={`/courses/${row.original.id}`}>
            {row.original.name}
          </Link>
          <p className="mt-1 text-xs text-muted-foreground">{row.original.code}</p>
        </div>
      ),
    },
    {
      id: "semester",
      accessorFn: (course) => `${course.semester} ${course.credits}`,
      header: "Semester / SKS",
      cell: ({ row }) => `${row.original.semester} · ${row.original.credits} SKS`,
    },
    {
      id: "actions",
      header: "Tindakan",
      enableSorting: false,
      cell: ({ row }) => (
        <div className="flex justify-end gap-2">
          {(user?.role === "superadmin" || row.original.created_by === user?.id) && (
            <>
              <Button aria-label={`Edit ${row.original.name}`} onClick={() => setDialog({ course: row.original })} size="sm" variant="outline">Edit</Button>
              <Button aria-label={`Hapus ${row.original.name}`} onClick={() => setDialog({ course: row.original, deleting: true })} size="sm" variant="destructive">Hapus</Button>
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
      <DataTableToolbar>
        <label className="grid w-full max-w-md gap-1.5 text-sm" htmlFor="course-search">
          Cari mata kuliah
          <Input
            id="course-search"
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Kode atau nama mata kuliah"
          type="search"
          value={search}
          />
        </label>
      </DataTableToolbar>
      {query.isPending || query.error ? (
        <QueryState query={query} />
      ) : rows.length === 0 ? (
        <NoData
          description={
            search
              ? "Tidak ada mata kuliah yang cocok dengan pencarian."
              : "Tambahkan mata kuliah atau lihat penugasan kelas Anda di sini."
          }
        />
      ) : (
        <DataTable columns={columns} data={rows} emptyMessage="Belum ada mata kuliah" getRowId={(course) => course.id} />
      )}
      {dialog && <CourseDialog {...dialog} close={() => setDialog(null)} />}
    </section>
  );
}
