import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Eye, Pencil, RefreshCw, Trash2 } from "lucide-react";
import type { ColumnDef } from "@tanstack/react-table";

import { DataTable } from "@/components/data-table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { QueryState } from "@/features/academic/Management";
import type { AcademicClass } from "@/features/academic/api";

interface CourseClassesTableProps {
  rows: AcademicClass[];
  isPending: boolean;
  isFetching: boolean;
  error: unknown;
  onRefresh: () => unknown;
  onEdit: (class_: AcademicClass) => void;
  onDelete: (class_: AcademicClass) => void;
}

/** Tabel presentasi; parent memasok kelas yang sudah terlingkup course dan pengguna. */
export function CourseClassesTable({ rows, isPending, isFetching, error, onRefresh, onEdit, onDelete }: CourseClassesTableProps) {
  const [search, setSearch] = useState("");
  const normalizedSearch = search.trim().toLocaleLowerCase("id-ID");
  const visibleRows = useMemo(() => rows.filter((row) =>
    `${row.section} ${row.academic_year}`.toLocaleLowerCase("id-ID").includes(normalizedSearch),
  ), [rows, normalizedSearch]);
  const columns = useMemo<ColumnDef<AcademicClass>[]>(() => [
    { accessorKey: "section", size: 28, header: "Kelas", cell: ({ row }) => <span className="block whitespace-normal text-wrap break-words font-medium">Kelas {row.original.section}</span> },
    { accessorKey: "academic_year", size: 26, header: "Tahun akademik", cell: ({ row }) => <span className="block whitespace-normal text-wrap break-words">{row.original.academic_year}</span> },
    { accessorKey: "has_finalized_grades", size: 26, header: "Status roster", cell: ({ row }) => <Badge variant={row.original.has_finalized_grades ? "secondary" : "outline"}>{row.original.has_finalized_grades ? "Roster terkunci" : "Roster terbuka"}</Badge> },
    { id: "actions", size: 20, header: "Tindakan", enableSorting: false, cell: ({ row }) => {
      const class_ = row.original;
      const label = `${class_.section} (${class_.academic_year})`;
      return (
        <div className="flex justify-end gap-2">
          <Button aria-label={`Lihat kelas ${label}`} render={<Link to={`/classes/${class_.id}`} />} size="icon" variant="outline"><Eye aria-hidden="true" className="size-4" /></Button>
          <Button aria-label={`Edit kelas ${label}`} className="border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100 hover:text-blue-800 dark:border-blue-900 dark:bg-blue-950/50 dark:text-blue-300 dark:hover:bg-blue-900/60" onClick={() => onEdit(class_)} size="icon" variant="outline"><Pencil aria-hidden="true" className="size-4" /></Button>
          <Button aria-label={`Hapus kelas ${label}`} onClick={() => onDelete(class_)} size="icon" variant="destructive"><Trash2 aria-hidden="true" className="size-4" /></Button>
        </div>
      );
    } },
  ], [onEdit, onDelete]);

  return (
    <>
      {Boolean(error) && <QueryState query={{ isPending, isFetching, error, refetch: onRefresh }} />}
      <DataTable
        columns={columns}
        data={visibleRows}
        getRowId={(row) => row.id}
        emptyMessage={isPending ? "Memuat data" : normalizedSearch ? "Tidak ada kelas yang cocok dengan pencarian." : "Belum ada kelas untuk mata kuliah ini."}
        search={<label className="flex items-center gap-2 whitespace-nowrap text-sm" htmlFor="course-classes-search">Cari<Input className="w-48 sm:w-64" id="course-classes-search" onChange={(event) => setSearch(event.target.value)} placeholder="Seksi atau tahun akademik" type="search" value={search} /></label>}
        actions={<Button aria-label="Segarkan" disabled={isFetching} onClick={() => void onRefresh()} type="button" variant="outline"><RefreshCw aria-hidden="true" className="size-4" /><span className="hidden sm:inline">Segarkan</span></Button>}
      />
    </>
  );
}
