import type { UserRole } from "./UsersPage";

interface UserSummaryRecord {
  role: UserRole;
  is_active: boolean;
}

/** Kartu ringkasan jumlah akun berdasarkan peran dan status aktif. */
export function UsersSummary({ users }: { users: UserSummaryRecord[] }) {
  const superadmins = users.filter((user) => user.role === "superadmin").length;
  const lecturers = users.filter((user) => user.role === "lecturer").length;
  const active = users.filter((user) => user.is_active).length;

  return (
    <div aria-label="Ringkasan pengguna" className="mb-5 grid gap-3 sm:grid-cols-3">
      <article className="rounded-xl border border-border bg-background p-4">
        <p className="text-sm text-muted-foreground">Total pengguna</p>
        <p className="mt-1 text-2xl font-semibold">{users.length}</p>
      </article>
      <article className="rounded-xl border border-border bg-background p-4">
        <p className="text-sm text-muted-foreground">Berdasarkan peran</p>
        <p className="mt-1 text-sm">Superadmin <strong>{superadmins}</strong> <span className="px-2 text-muted-foreground">|</span> Dosen <strong>{lecturers}</strong></p>
      </article>
      <article className="rounded-xl border border-border bg-background p-4">
        <p className="text-sm text-muted-foreground">Berdasarkan status</p>
        <p className="mt-1 text-sm">Aktif <strong>{active}</strong> <span className="px-2 text-muted-foreground">|</span> Nonaktif <strong>{users.length - active}</strong></p>
      </article>
    </div>
  );
}
