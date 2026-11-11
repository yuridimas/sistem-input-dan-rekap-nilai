/**
 * Pengelolaan keikutsertaan mahasiswa pada halaman kelas.
 * Operasi enrollment terpisah dari perubahan profil global dan tunduk penguncian nilai final.
 */
import { useMemo, useState } from "react";
import { Eye, Plus, RefreshCw, Trash2 } from "lucide-react";
import { Link } from "react-router-dom";
import type { ColumnDef } from "@tanstack/react-table";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FieldGroup } from "@/components/ui/field";
import { DataTable } from "@/components/data-table";
import {
  MutationDialog,
  QueryState,
  TextField,
} from "@/features/academic/Management";
import {
  fieldError,
  useAcademicMutation,
  useAcademicQuery,
  type RosterEntry,
  type Student,
} from "@/features/academic/api";
import api from "@/lib/api";

/**
 * Pakai profil NIM yang sudah ada; kirim nama/email hanya untuk mahasiswa baru.
 */
function EnrollmentDialog({
  classId,
  close,
}: {
  classId: string;
  close: () => void;
}) {
  const students = useAcademicQuery<Student[]>("/students");
  const [nim, setNim] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const existing = students.data?.find((row) => row.nim === nim.trim());
  const mutation = useAcademicMutation(
    () =>
      api.post(`/classes/${classId}/enrollments`, {
        nim: nim.trim(),
        ...(existing
          ? {}
          : { full_name: name.trim(), email: email.trim() || null }),
      }),
    close,
  );
  return (
    <MutationDialog
      busy={mutation.isPending}
      close={close}
      description="Masukkan NIM. Mahasiswa terdaftar memakai data yang sudah ada; mahasiswa baru wajib memiliki nama lengkap."
      error={mutation.error}
      onSubmit={(event) => {
        event.preventDefault();
        mutation.mutate();
      }}
      submitDisabled={students.isPending || Boolean(students.error)}
      submitLabel="Daftarkan mahasiswa"
      title="Tambah mahasiswa ke kelas"
    >
      <FieldGroup>
        <TextField
          error={fieldError(mutation.error, "nim")}
          label="NIM"
          maxLength={50}
          onChange={(event) => setNim(event.target.value)}
          required
          value={nim}
        />
        {students.isPending || students.error ? (
          <QueryState query={students} />
        ) : existing ? (
          <Alert>
            <AlertTitle>{existing.full_name}</AlertTitle>
            <AlertDescription>
              {existing.email || "Email belum tersedia"}. Data mahasiswa
              tersimpan akan digunakan.
            </AlertDescription>
          </Alert>
        ) : (
          <>
            <TextField
              error={fieldError(mutation.error, "full_name")}
              label="Nama lengkap mahasiswa baru"
              maxLength={255}
              onChange={(event) => setName(event.target.value)}
              required
              value={name}
            />
            <TextField
              error={fieldError(mutation.error, "email")}
              label="Email (opsional)"
              maxLength={255}
              onChange={(event) => setEmail(event.target.value)}
              type="email"
              value={email}
            />
          </>
        )}
      </FieldGroup>
    </MutationDialog>
  );
}

/**
 * Konfirmasi penghapusan enrollment tanpa menghapus profil mahasiswa global.
 */
function RemoveEnrollmentDialog({
  classId,
  row,
  close,
}: {
  classId: string;
  row: RosterEntry;
  close: () => void;
}) {
  const mutation = useAcademicMutation(
    () => api.delete(`/classes/${classId}/enrollments/${row.id}`),
    close,
  );
  return (
    <MutationDialog
      busy={mutation.isPending}
      close={close}
      description={`Keluarkan ${row.student.full_name} (${row.student.nim}) dari kelas? Data mahasiswa tetap tersedia di daftar mahasiswa. Enrollment yang sudah memiliki nilai tidak dapat dihapus.`}
      destructive
      error={mutation.error}
      onSubmit={(event) => {
        event.preventDefault();
        mutation.mutate();
      }}
      submitLabel="Keluarkan mahasiswa"
      title="Keluarkan mahasiswa dari kelas"
    />
  );
}

/**
 * Sajikan anggota kelas dan tindakan roster; locked menahan perubahan setelah finalisasi.
 */
export function Roster({
  classId,
  locked,
}: {
  classId: string;
  locked: boolean;
}) {
  const query = useAcademicQuery<RosterEntry[]>(`/classes/${classId}/roster`);
  const [adding, setAdding] = useState(false);
  const [removing, setRemoving] = useState<RosterEntry | null>(null);
  const [search, setSearch] = useState("");
  const normalizedSearch = search.trim().toLocaleLowerCase("id-ID");
  const rows = useMemo(() => (query.data ?? []).filter((row) =>
    `${row.student.full_name} ${row.student.nim} ${row.student.email ?? ""}`.toLocaleLowerCase("id-ID").includes(normalizedSearch),
  ), [query.data, normalizedSearch]);
  const columns = useMemo<ColumnDef<RosterEntry>[]>(() => [
    {
      id: "student",
      size: 40,
      accessorFn: (entry) => `${entry.student.full_name} ${entry.student.nim}`,
      header: "Mahasiswa",
      cell: ({ row }) => (
        <div className="min-w-0 whitespace-normal text-wrap break-words">
          <span className="font-medium">
            {row.original.student.full_name}
          </span>
          <p className="mt-1 text-xs text-muted-foreground">{row.original.student.nim}</p>
        </div>
      ),
    },
    {
      id: "email",
      size: 38,
      accessorFn: (entry) => entry.student.email ?? "",
      header: "Email",
      cell: ({ row }) => <span className="block min-w-0 whitespace-normal text-wrap break-all">{row.original.student.email || "—"}</span>,
    },
    {
      id: "actions",
      size: 22,
      header: "Tindakan",
      enableSorting: false,
      cell: ({ row }) => (
        <div className="flex justify-end gap-2">
          <Button aria-label={`Lihat mahasiswa ${row.original.student.full_name} (${row.original.student.nim})`} render={<Link to={`/students/${row.original.student.id}`} />} size="icon" variant="outline"><Eye aria-hidden="true" className="size-4" /></Button>
          {!locked && <Button aria-label={`Keluarkan ${row.original.student.full_name}`} onClick={() => setRemoving(row.original)} size="icon" variant="destructive">
            <Trash2 aria-hidden="true" className="size-4" />
          </Button>}
        </div>
      ),
    },
  ], [locked]);
  return (
    <section className="flex flex-col gap-5" aria-labelledby="roster-title">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-semibold" id="roster-title">
          Daftar mahasiswa kelas
        </h2>
        <Button disabled={locked} onClick={() => setAdding(true)}>
          <Plus data-icon="inline-start" />
          Tambah mahasiswa ke kelas
        </Button>
      </div>
      {query.error && <QueryState query={query} />}
      <DataTable
        columns={columns}
        data={rows}
        getRowId={(row) => row.id}
        emptyMessage={query.isPending ? "Memuat data" : normalizedSearch ? "Tidak ada mahasiswa yang cocok dengan pencarian." : "Belum ada mahasiswa di kelas ini."}
        search={<label className="flex items-center gap-2 whitespace-nowrap text-sm" htmlFor={`roster-search-${classId}`}>Cari<Input className="w-48 sm:w-64" id={`roster-search-${classId}`} onChange={(event) => setSearch(event.target.value)} placeholder="Nama, NIM, atau email" type="search" value={search} /></label>}
        actions={<Button aria-label="Segarkan" disabled={query.isFetching} onClick={() => void query.refetch()} type="button" variant="outline"><RefreshCw aria-hidden="true" className="size-4" /><span className="hidden sm:inline">Segarkan</span></Button>}
      />
      {adding && !locked && (
        <EnrollmentDialog classId={classId} close={() => setAdding(false)} />
      )}
      {removing && !locked && (
        <RemoveEnrollmentDialog
          classId={classId}
          close={() => setRemoving(null)}
          row={removing}
        />
      )}
    </section>
  );
}
