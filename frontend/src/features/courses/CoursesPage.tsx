/**
 * Daftar mata kuliah terotorisasi beserta pencarian lokal dan dialog pengelolaan.
 * Data berasal dari query akademik per pengguna; backend menentukan cakupan daftar.
 */
import { useState } from "react";
import { Link } from "react-router-dom";
import { Plus } from "lucide-react";

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
      <div className="mb-5 max-w-md">
        <TextField
          label="Cari mata kuliah"
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Kode atau nama mata kuliah"
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
              ? "Tidak ada mata kuliah yang cocok dengan pencarian."
              : "Tambahkan mata kuliah atau lihat penugasan kelas Anda di sini."
          }
        />
      ) : (
        <div className="overflow-hidden rounded-xl border bg-background">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Mata kuliah</TableHead>
                <TableHead>Semester / SKS</TableHead>
                <TableHead className="text-right">Tindakan</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((course) => (
                <TableRow key={course.id}>
                  <TableCell className="max-w-72 whitespace-normal">
                    <Link
                      className="font-medium underline-offset-4 hover:underline"
                      to={`/courses/${course.id}`}
                    >
                      {course.name}
                    </Link>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {course.code}
                    </p>
                  </TableCell>
                  <TableCell>
                    {course.semester} · {course.credits} SKS
                  </TableCell>
                  <TableCell>
                    <div className="flex justify-end gap-2">
                      {(user?.role === "superadmin" ||
                        course.created_by === user?.id) && (
                        <>
                          <Button
                            aria-label={`Edit ${course.name}`}
                            onClick={() => setDialog({ course })}
                            size="sm"
                            variant="outline"
                          >
                            Edit
                          </Button>
                          <Button
                            aria-label={`Hapus ${course.name}`}
                            onClick={() =>
                              setDialog({ course, deleting: true })
                            }
                            size="sm"
                            variant="destructive"
                          >
                            Hapus
                          </Button>
                        </>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
      {dialog && <CourseDialog {...dialog} close={() => setDialog(null)} />}
    </section>
  );
}
