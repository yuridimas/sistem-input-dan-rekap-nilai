import { useState } from "react";
import { Plus } from "lucide-react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  NoData,
  PageHeader,
  QueryState,
  TextField,
} from "@/features/academic/Management";
import { useAcademicQuery, type Student } from "@/features/academic/api";
import { useAuth } from "@/features/auth/useAuth";
import { StudentDialog } from "./StudentDialog";

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
      <div className="mb-5 max-w-md">
        <TextField
          label="Cari mahasiswa"
          onChange={(event) => setSearch(event.target.value)}
          placeholder="NIM atau nama lengkap"
          type="search"
          value={search}
        />
      </div>
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
        <div className="overflow-hidden rounded-xl border bg-background">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Mahasiswa</TableHead>
                <TableHead>Email</TableHead>
                {user?.role === "superadmin" && (
                  <TableHead className="text-right">Tindakan</TableHead>
                )}
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((student) => (
                <TableRow key={student.id}>
                  <TableCell className="max-w-72 whitespace-normal">
                    <Link
                      className="font-medium underline-offset-4 hover:underline"
                      to={`/students/${student.id}`}
                    >
                      {student.full_name}
                    </Link>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {student.nim}
                    </p>
                  </TableCell>
                  <TableCell className="max-w-64 break-all whitespace-normal">
                    {student.email || "—"}
                  </TableCell>
                  {user?.role === "superadmin" && (
                    <TableCell>
                      <div className="flex justify-end gap-2">
                        <Button
                          aria-label={`Edit ${student.full_name}`}
                          onClick={() => setDialog({ student })}
                          size="sm"
                          variant="outline"
                        >
                          Edit
                        </Button>
                        <Button
                          aria-label={`Hapus ${student.full_name}`}
                          onClick={() => setDialog({ student, deleting: true })}
                          size="sm"
                          variant="destructive"
                        >
                          Hapus
                        </Button>
                      </div>
                    </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
      {dialog && <StudentDialog {...dialog} close={() => setDialog(null)} />}
    </section>
  );
}
