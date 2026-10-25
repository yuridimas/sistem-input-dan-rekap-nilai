import { useState } from "react";

import { FieldGroup } from "@/components/ui/field";
import api from "@/lib/api";
import { MutationDialog, TextField } from "@/features/academic/Management";
import {
  fieldError,
  useAcademicMutation,
  type Course,
} from "@/features/academic/api";

export function CourseDialog({
  course,
  close,
  deleting = false,
}: {
  course?: Course;
  close: () => void;
  deleting?: boolean;
}) {
  const [form, setForm] = useState({
    code: course?.code ?? "",
    name: course?.name ?? "",
    credits: String(course?.credits ?? 3),
    semester: course?.semester ?? "",
  });
  const mutation = useAcademicMutation(async () => {
    if (deleting) return api.delete(`/courses/${course!.id}`);
    const payload = {
      ...form,
      code: form.code.trim(),
      name: form.name.trim(),
      semester: form.semester.trim(),
      credits: Number(form.credits),
    };
    return course
      ? api.patch(`/courses/${course.id}`, payload)
      : api.post("/courses", payload);
  }, close);
  const set = (name: keyof typeof form, value: string) =>
    setForm({ ...form, [name]: value });
  return (
    <MutationDialog
      busy={mutation.isPending}
      close={close}
      destructive={deleting}
      description={
        deleting
          ? `Hapus mata kuliah ${course?.name}? Mata kuliah yang masih memiliki kelas tidak dapat dihapus.`
          : "Lengkapi identitas mata kuliah."
      }
      error={mutation.error}
      onSubmit={(event) => {
        event.preventDefault();
        mutation.mutate();
      }}
      submitLabel={deleting ? "Hapus mata kuliah" : "Simpan mata kuliah"}
      title={
        deleting
          ? "Hapus mata kuliah"
          : course
            ? "Edit mata kuliah"
            : "Tambah mata kuliah"
      }
    >
      {!deleting && (
        <FieldGroup>
          {(
            [
              ["code", "Kode mata kuliah", 50],
              ["name", "Nama mata kuliah", 255],
              ["semester", "Semester", 20],
            ] as const
          ).map(([name, label, maxLength]) => (
            <TextField
              error={fieldError(mutation.error, name)}
              key={name}
              label={label}
              maxLength={maxLength}
              onChange={(event) => set(name, event.target.value)}
              placeholder={name === "semester" ? "2026/1" : undefined}
              required
              value={form[name]}
            />
          ))}
          <TextField
            error={fieldError(mutation.error, "credits")}
            label="Jumlah SKS"
            min={1}
            onChange={(event) => set("credits", event.target.value)}
            required
            step={1}
            type="number"
            value={form.credits}
          />
        </FieldGroup>
      )}
    </MutationDialog>
  );
}
