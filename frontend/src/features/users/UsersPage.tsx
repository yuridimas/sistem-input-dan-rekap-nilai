/** Daftar akun administratif yang dapat ditinjau superadmin. */
import { useMemo, useState } from "react";
import { RefreshCw } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import type { ColumnDef } from "@tanstack/react-table";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select";
import { DataTable } from "@/components/data-table";
import { PageHeader, QueryState } from "@/features/academic/Management";
import { useAuth } from "@/features/auth/useAuth";
import api from "@/lib/api";
import { UsersSummary } from "./UsersSummary";

export type UserRole = "superadmin" | "lecturer";
type RoleFilter = "all" | UserRole;
type ActiveFilter = "all" | "true" | "false";

interface UserRecord {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

const roleLabels: Record<UserRole, string> = {
  superadmin: "Superadmin",
  lecturer: "Dosen",
};

function dateLabel(value: string) {
  return new Intl.DateTimeFormat("id-ID", { dateStyle: "medium" }).format(new Date(value));
}

const columns: ColumnDef<UserRecord>[] = [
  { accessorKey: "full_name", size: 22, header: "Nama", cell: ({ row }) => <span className="font-medium">{row.original.full_name}</span> },
  { accessorKey: "email", size: 28, header: "Email", cell: ({ row }) => <span className="break-all">{row.original.email}</span> },
  { accessorKey: "role", size: 14, header: "Peran", cell: ({ row }) => roleLabels[row.original.role] },
  { accessorKey: "is_active", size: 14, header: "Status", cell: ({ row }) => (
    <Badge variant={row.original.is_active ? "secondary" : "outline"}>
      {row.original.is_active ? "Aktif" : "Nonaktif"}
    </Badge>
  ) },
  { accessorKey: "created_at", size: 22, header: "Dibuat", cell: ({ row }) => (
    <span className="whitespace-nowrap">{dateLabel(row.original.created_at)}</span>
  ) },
];

/** Tampilkan akun tanpa membuka field kredensial yang tidak termasuk kontrak publik. */
export function UsersPage() {
  const { user } = useAuth();
  const [role, setRole] = useState<RoleFilter>("all");
  const [active, setActive] = useState<ActiveFilter>("all");
  const [search, setSearch] = useState("");
  const params = useMemo(() => ({
    ...(role === "all" ? {} : { role }),
    ...(active === "all" ? {} : { is_active: active === "true" }),
  }), [active, role]);
  const query = useQuery({
    queryKey: ["users", user?.id, role, active],
    queryFn: async () => (await api.get<UserRecord[]>("/admin/users", {
      params: Object.keys(params).length ? params : undefined,
    })).data,
    enabled: Boolean(user),
    retry: false,
  });

  const users = query.data ?? [];
  const normalizedSearch = search.trim().toLocaleLowerCase("id-ID");
  const visibleUsers = users.filter((record) =>
    `${record.full_name} ${record.email}`.toLocaleLowerCase("id-ID").includes(normalizedSearch),
  );

  return (
    <section className="mx-auto max-w-6xl">
      <PageHeader description="Lihat akun yang tersedia untuk pengujian manual." title="Pengguna" />

      {!query.isPending && !query.error && <UsersSummary users={visibleUsers} />}

      {query.error && <QueryState query={query} />}
      <DataTable
          actions={<Button aria-label="Segarkan" disabled={query.isFetching} onClick={() => void query.refetch()} type="button" variant="outline"><RefreshCw aria-hidden="true" className="size-4" /><span className="hidden sm:inline">Segarkan</span></Button>}
          columns={columns}
          data={visibleUsers}
          emptyMessage={query.isPending ? "Memuat data" : users.length ? "Tidak ada pengguna yang cocok dengan pencarian." : "Belum ada pengguna"}
          getRowId={(record) => record.id}
          search={<label className="grid w-full gap-1.5 text-sm sm:w-64" htmlFor="users-search">Cari pengguna<Input autoComplete="off" id="users-search" onChange={(event) => setSearch(event.target.value)} placeholder="Nama atau email" type="search" value={search} /></label>}
          toolbar={<div className="flex flex-wrap items-end gap-3"><label className="grid gap-1.5 text-sm" htmlFor="users-role-filter">Peran<NativeSelect id="users-role-filter" onChange={(event) => setRole(event.target.value as RoleFilter)} value={role}><NativeSelectOption value="all">Semua peran</NativeSelectOption><NativeSelectOption value="superadmin">Superadmin</NativeSelectOption><NativeSelectOption value="lecturer">Dosen</NativeSelectOption></NativeSelect></label><label className="grid gap-1.5 text-sm" htmlFor="users-active-filter">Status<NativeSelect id="users-active-filter" onChange={(event) => setActive(event.target.value as ActiveFilter)} value={active}><NativeSelectOption value="all">Semua status</NativeSelectOption><NativeSelectOption value="true">Aktif</NativeSelectOption><NativeSelectOption value="false">Nonaktif</NativeSelectOption></NativeSelect></label></div>}
        />
    </section>
  );
}
