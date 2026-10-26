/**
 * Dialog profil mahasiswa global dari halaman StudentsPage.
 * Penghapusan profil berbeda dari mengeluarkan mahasiswa dari roster kelas.
 */
import { useState } from "react";

import { FieldGroup } from "@/components/ui/field";
import { MutationDialog, TextField } from "@/features/academic/Management";
import {
  fieldError,
  useAcademicMutation,
  type Student,
} from "@/features/academic/api";
import api from "@/lib/api";

/**
 * Kirim email kosong sebagai null; pilih create/update/delete sesuai props dan laporkan
 * error field.
 */
export function StudentDialog({
  student,
  deleting = false,
  close,
}: {
  student?: Student;
  deleting?: boolean;
  close: () => void;
}) {
  const [nim, setNim] = useState(student?.nim ?? "");
  const [name, setName] = useState(student?.full_name ?? "");
  const [email, setEmail] = useState(student?.email ?? "");
  const mutation = useAcademicMutation(async () => {
    if (deleting) return api.delete(`/students/${student!.id}`);
    const payload = {
      nim: nim.trim(),
      full_name: name.trim(),
      email: email.trim() || null,
    };
    return student
      ? api.patch(`/students/${student.id}`, payload)
      : api.post("/students", payload);
  }, close);
  return (
    <MutationDialog
      busy={mutation.isPending}
      close={close}
      description={
        deleting
          ? `Hapus ${student?.full_name}? Mahasiswa yang masih terdaftar di kelas tidak dapat dihapus.`
          : "Data mahasiswa dipakai bersama oleh seluruh kelas. Email bersifat opsional."
      }
      destructive={deleting}
      error={mutation.error}
      onSubmit={(event) => {
        event.preventDefault();
        mutation.mutate();
      }}
      submitLabel={deleting ? "Hapus mahasiswa" : "Simpan mahasiswa"}
      title={
        deleting
          ? "Hapus mahasiswa"
          : student
            ? "Edit mahasiswa"
            : "Tambah mahasiswa"
      }
    >
      {!deleting && (
        <FieldGroup>
          <TextField
            error={fieldError(mutation.error, "nim")}
            label="NIM"
            maxLength={50}
            onChange={(event) => setNim(event.target.value)}
            required
            value={nim}
          />
          <TextField
            error={fieldError(mutation.error, "full_name")}
            label="Nama lengkap"
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
        </FieldGroup>
      )}
    </MutationDialog>
  );
}
