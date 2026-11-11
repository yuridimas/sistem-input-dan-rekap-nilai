import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { FieldGroup } from "@/components/ui/field";
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select";
import { MutationDialog, TextField } from "@/features/academic/Management";
import { fieldError } from "@/features/academic/api";
import api from "@/lib/api";

import type { UserRecord, UserRole } from "./types";

/** Form tambah/edit akun administratif dan konfirmasi nonaktifkan. */
export function UserDialog({
  user,
  deleting = false,
  close,
}: {
  user?: UserRecord;
  deleting?: boolean;
  close: () => void;
}) {
  const queryClient = useQueryClient();
  const [email, setEmail] = useState(user?.email ?? "");
  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<UserRole>(user?.role ?? "lecturer");
  const [active, setActive] = useState(user?.is_active ?? true);
  const mutation = useMutation({
    mutationFn: async () => {
      if (deleting) return api.delete(`/admin/users/${user!.id}`);
      if (user) {
        return api.patch(`/admin/users/${user.id}`, {
          email: email.trim(),
          full_name: fullName.trim(),
          role,
          is_active: active,
          ...(password ? { password } : {}),
        });
      }
      return api.post("/admin/users", {
        email: email.trim(),
        full_name: fullName.trim(),
        password,
        role,
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["users"] });
      close();
    },
  });

  return (
    <MutationDialog
      busy={mutation.isPending}
      close={close}
      destructive={deleting}
      description={deleting
        ? `Nonaktifkan akun ${user?.full_name}? Akun dan riwayatnya tetap tersimpan.`
        : "Lengkapi informasi akun pengguna."}
      error={mutation.error}
      onSubmit={(event) => {
        event.preventDefault();
        mutation.mutate();
      }}
      submitLabel={deleting ? "Nonaktifkan pengguna" : "Simpan pengguna"}
      title={deleting ? "Nonaktifkan pengguna" : user ? "Edit pengguna" : "Tambah pengguna"}
    >
      {!deleting && (
        <FieldGroup>
          <TextField
            error={fieldError(mutation.error, "full_name")}
            label="Nama lengkap"
            maxLength={255}
            onChange={(event) => setFullName(event.target.value)}
            required
            value={fullName}
          />
          <TextField
            error={fieldError(mutation.error, "email")}
            label="Email akun"
            maxLength={255}
            onChange={(event) => setEmail(event.target.value)}
            required
            type="email"
            value={email}
          />
          <TextField
            error={fieldError(mutation.error, "password")}
            label={user ? "Kata sandi baru (opsional)" : "Kata sandi"}
            minLength={6}
            onChange={(event) => setPassword(event.target.value)}
            required={!user}
            type="password"
            value={password}
          />
          <label className="grid gap-1.5 text-sm" htmlFor="user-role">
            Peran
            <NativeSelect id="user-role" onChange={(event) => setRole(event.target.value as UserRole)} value={role}>
              <NativeSelectOption value="lecturer">Dosen</NativeSelectOption>
              <NativeSelectOption value="superadmin">Superadmin</NativeSelectOption>
            </NativeSelect>
          </label>
          {user && (
            <label className="grid gap-1.5 text-sm" htmlFor="user-active">
              Status
              <NativeSelect id="user-active" onChange={(event) => setActive(event.target.value === "true")} value={String(active)}>
                <NativeSelectOption value="true">Aktif</NativeSelectOption>
                <NativeSelectOption value="false">Nonaktif</NativeSelectOption>
              </NativeSelect>
            </label>
          )}
        </FieldGroup>
      )}
    </MutationDialog>
  );
}
