import { useId, useState } from "react";

import { Field, FieldGroup, FieldLabel } from "@/components/ui/field";
import {
  NativeSelect,
  NativeSelectOption,
} from "@/components/ui/native-select";
import {
  MutationDialog,
  QueryState,
  TextField,
} from "@/features/academic/Management";
import {
  fieldError,
  useAcademicMutation,
  useAcademicQuery,
  type AcademicClass,
  type Lecturer,
} from "@/features/academic/api";
import { useAuth } from "@/features/auth/useAuth";
import api from "@/lib/api";

export function ClassDialog({
  courseId,
  class_,
  deleting = false,
  close,
  afterDelete,
}: {
  courseId: string;
  class_?: AcademicClass;
  deleting?: boolean;
  close: () => void;
  afterDelete?: () => void;
}) {
  const { user } = useAuth();
  const admin = user?.role === "superadmin";
  const lecturerId = useId();
  const lecturers = useAcademicQuery<Lecturer[]>(
    "/admin/users?role=lecturer",
    admin && !deleting,
  );
  const [section, setSection] = useState(class_?.section ?? "");
  const [year, setYear] = useState(class_?.academic_year ?? "");
  const [lecturer, setLecturer] = useState(class_?.lecturer_id ?? "");
  const mutation = useAcademicMutation(
    async () => {
      if (deleting) return api.delete(`/classes/${class_!.id}`);
      const payload = {
        section: section.trim(),
        academic_year: year.trim(),
        ...(admin ? { lecturer_id: lecturer } : {}),
      };
      return class_
        ? api.patch(`/classes/${class_.id}`, payload)
        : api.post("/classes", { ...payload, course_id: courseId });
    },
    () => {
      close();
      if (deleting) afterDelete?.();
    },
  );
  return (
    <MutationDialog
      busy={mutation.isPending}
      close={close}
      description={
        deleting
          ? "Kelas yang masih memiliki mahasiswa atau komponen penilaian tidak dapat dihapus."
          : "Tentukan seksi, tahun akademik, dan dosen pengampu."
      }
      destructive={deleting}
      error={mutation.error}
      onSubmit={(event) => {
        event.preventDefault();
        mutation.mutate();
      }}
      submitDisabled={
        !deleting &&
        admin &&
        (lecturers.isPending || Boolean(lecturers.error) || !lecturer)
      }
      submitLabel={deleting ? "Hapus kelas" : "Simpan kelas"}
      title={
        deleting
          ? `Hapus kelas ${class_?.section}`
          : class_
            ? "Edit kelas"
            : "Tambah kelas"
      }
    >
      {!deleting && (
        <FieldGroup>
          <TextField
            error={fieldError(mutation.error, "section")}
            label="Seksi kelas"
            maxLength={10}
            onChange={(event) => setSection(event.target.value)}
            placeholder="A"
            required
            value={section}
          />
          <TextField
            error={fieldError(mutation.error, "academic_year")}
            label="Tahun akademik"
            maxLength={20}
            onChange={(event) => setYear(event.target.value)}
            placeholder="2026/2027"
            required
            value={year}
          />
          {admin && (
            <>
              <Field>
                <FieldLabel htmlFor={lecturerId}>Dosen pengampu</FieldLabel>
                <NativeSelect
                  className="w-full"
                  id={lecturerId}
                  onChange={(event) => setLecturer(event.target.value)}
                  required
                  value={lecturer}
                >
                  <NativeSelectOption value="">Pilih dosen</NativeSelectOption>
                  {lecturers.data?.map((row) => (
                    <NativeSelectOption key={row.id} value={row.id}>
                      {row.full_name} · {row.email}
                      {row.is_active ? "" : " (nonaktif)"}
                    </NativeSelectOption>
                  ))}
                </NativeSelect>
              </Field>
              {(lecturers.isPending || lecturers.error) && (
                <QueryState query={lecturers} />
              )}
            </>
          )}
        </FieldGroup>
      )}
    </MutationDialog>
  );
}
