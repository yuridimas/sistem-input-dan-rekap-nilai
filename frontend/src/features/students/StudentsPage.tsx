/**
 * Daftar profil global mahasiswa dengan pencarian NIM/nama dan tautan riwayat.
 * Pembuatan tersedia untuk dosen/admin; perubahan profil ditampilkan hanya bagi superadmin.
 */
import { useMemo, useState } from "react";
import { Pencil, Plus, RefreshCw, Trash2 } from "lucide-react";
import { Link } from "react-router-dom";
import type { ColumnDef } from "@tanstack/react-table";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { DataTable } from "@/components/data-table";
import {
  PageHeader,
  QueryState,
} from "@/features/academic/Management";
import { useAcademicQuery, type Student } from "@/features/academic/api";
import { useAuth } from "@/features/auth/useAuth";
import { StudentDialog } from "./StudentDialog";

/**
 * Kelola filter lokal dan pemilihan dialog sambil mempertahankan state query
 * loading/error.
 */
export function StudentsPage() {
  const { user } = useAuth();
  const query = useAcademicQuery<Student[]>("/students");
  const [search, setSearch] = useState("");
  const [dialog, setDialog] = useState<{
    student?: Student;
    deleting?: boolean;
  } | null>(null);
  const rows =
    query.data?.filter((row) =>
      `${row.nim} ${row.full_name}`
        .toLowerCase()
        .includes(search.toLowerCase()),
    ) ?? [];
  const columns = useMemo<ColumnDef<Student>[]>(() => [
    {
      id: "student",
      size: 40,
      accessorFn: (student) => `${student.full_name} ${student.nim}`,
      header: "Mahasiswa",
      cell: ({ row }) => (
        <div className="max-w-72 whitespace-normal">
          <Link className="font-medium underline-offset-4 hover:underline" to={`/students/${row.original.id}`}>
            {row.original.full_name}
          </Link>
          <p className="mt-1 text-xs text-muted-foreground">{row.original.nim}</p>
        </div>
      ),
    },
    {
      accessorKey: "email",
      size: 35,
      header: "Email",
      cell: ({ row }) => <span className="max-w-64 break-all whitespace-normal">{row.original.email || "—"}</span>,
    },
    ...(user?.role === "superadmin" ? [{
      id: "actions",
      size: 25,
      header: "Tindakan",
      enableSorting: false,
      cell: ({ row }: { row: { original: Student } }) => (
        <div className="flex justify-end gap-2">
          <Button aria-label={`Edit ${row.original.full_name}`} onClick={() => setDialog({ student: row.original })} size="icon" variant="outline"><Pencil aria-hidden="true" className="size-4" /></Button>
          <Button aria-label={`Hapus ${row.original.full_name}`} onClick={() => setDialog({ student: row.original, deleting: true })} size="icon" variant="destructive"><Trash2 aria-hidden="true" className="size-4" /></Button>
        </div>
      ),
    }] : []),
  ], [user?.role]);
  return (
    <section className="mx-auto max-w-6xl">
      <PageHeader
        description="Daftar mahasiswa bersama untuk seluruh mata kuliah dan kelas."
        title="Mahasiswa"
      >
        <Button onClick={() => setDialog({})}>
          <Plus data-icon="inline-start" />
          Tambah mahasiswa
        </Button>
      </PageHeader>
      {query.error && <QueryState query={query} />}
      <DataTable
          actions={<Button aria-label="Segarkan" disabled={query.isFetching} onClick={() => void query.refetch()} type="button" variant="outline"><RefreshCw aria-hidden="true" className="size-4" /><span className="hidden sm:inline">Segarkan</span></Button>}
          columns={columns}
          data={rows}
          emptyMessage={query.isPending ? "Memuat data" : search ? "Tidak ada mahasiswa yang cocok dengan pencarian." : "Belum ada mahasiswa"}
          getRowId={(student) => student.id}
          search={<label className="grid w-full gap-1.5 text-sm sm:w-64" htmlFor="student-search">Cari mahasiswa<Input id="student-search" onChange={(event) => setSearch(event.target.value)} placeholder="NIM atau nama lengkap" type="search" value={search} /></label>}
        />
      {dialog && <StudentDialog {...dialog} close={() => setDialog(null)} />}
    </section>
  );
}
