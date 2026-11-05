/**
 * Daftar profil global mahasiswa dengan pencarian NIM/nama dan tautan riwayat.
 * Pembuatan tersedia untuk dosen/admin; perubahan profil ditampilkan hanya bagi superadmin.
 */
import { useMemo, useState } from "react";
import { Plus } from "lucide-react";
import { Link } from "react-router-dom";
import type { ColumnDef } from "@tanstack/react-table";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { DataTable, DataTableToolbar } from "@/components/data-table";
import {
  NoData,
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
      header: "Email",
      cell: ({ row }) => <span className="max-w-64 break-all whitespace-normal">{row.original.email || "—"}</span>,
    },
    ...(user?.role === "superadmin" ? [{
      id: "actions",
      header: "Tindakan",
      enableSorting: false,
      cell: ({ row }: { row: { original: Student } }) => (
        <div className="flex justify-end gap-2">
          <Button aria-label={`Edit ${row.original.full_name}`} onClick={() => setDialog({ student: row.original })} size="sm" variant="outline">Edit</Button>
          <Button aria-label={`Hapus ${row.original.full_name}`} onClick={() => setDialog({ student: row.original, deleting: true })} size="sm" variant="destructive">Hapus</Button>
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
      <DataTableToolbar>
        <label className="grid w-full max-w-md gap-1.5 text-sm" htmlFor="student-search">
          Cari mahasiswa
          <Input
            id="student-search"
          onChange={(event) => setSearch(event.target.value)}
          placeholder="NIM atau nama lengkap"
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
              ? "Tidak ada mahasiswa yang cocok dengan pencarian."
              : "Tambahkan mahasiswa atau daftarkan NIM melalui roster kelas."
          }
        />
      ) : (
        <DataTable columns={columns} data={rows} emptyMessage="Belum ada mahasiswa" getRowId={(student) => student.id} />
      )}
      {dialog && <StudentDialog {...dialog} close={() => setDialog(null)} />}
    </section>
  );
}
