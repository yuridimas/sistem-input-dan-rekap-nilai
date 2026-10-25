import { useState } from "react";
import { Plus } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { FieldGroup } from "@/components/ui/field";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  MutationDialog,
  NoData,
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
      {query.isPending || query.error ? (
        <QueryState query={query} />
      ) : !query.data?.length ? (
        <NoData description="Daftarkan mahasiswa dengan NIM untuk mulai mengisi roster kelas." />
      ) : (
        <div className="overflow-hidden rounded-xl border bg-background">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Mahasiswa</TableHead>
                <TableHead>Email</TableHead>
                {!locked && (
                  <TableHead className="text-right">Tindakan</TableHead>
                )}
              </TableRow>
            </TableHeader>
            <TableBody>
              {query.data.map((row) => (
                <TableRow key={row.id}>
                  <TableCell className="max-w-64 whitespace-normal">
                    <p className="font-medium">{row.student.full_name}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {row.student.nim}
                    </p>
                  </TableCell>
                  <TableCell className="max-w-56 break-all whitespace-normal">
                    {row.student.email || "—"}
                  </TableCell>
                  {!locked && (
                    <TableCell className="text-right">
                      <Button
                        aria-label={`Keluarkan ${row.student.full_name}`}
                        onClick={() => setRemoving(row)}
                        size="sm"
                        variant="destructive"
                      >
                        Keluarkan
                      </Button>
                    </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
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
