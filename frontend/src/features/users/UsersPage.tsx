/** Daftar akun administratif yang dapat ditinjau superadmin. */
import { useMemo, useState } from "react";
import { Pencil, Plus, RefreshCw, RotateCcw, Trash2 } from "lucide-react";
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
import { UserDialog } from "./UserDialog";
import type { UserRecord, UserRole } from "./types";

type RoleFilter = "all" | UserRole;
type ActiveFilter = "all" | "true" | "false";

const roleLabels: Record<UserRole, string> = {
  superadmin: "Superadmin",
  lecturer: "Dosen",
};

function dateLabel(value: string) {
  return new Intl.DateTimeFormat("id-ID", { dateStyle: "medium" }).format(new Date(value));
}

/** Tampilkan akun tanpa membuka field kredensial yang tidak termasuk kontrak publik. */
export function UsersPage() {
  const { user } = useAuth();
  const [role, setRole] = useState<RoleFilter>("all");
  const [active, setActive] = useState<ActiveFilter>("all");
  const [draftRole, setDraftRole] = useState<RoleFilter>("all");
  const [draftActive, setDraftActive] = useState<ActiveFilter>("all");
  const [search, setSearch] = useState("");
  const [dialog, setDialog] = useState<{ user?: UserRecord; deleting?: boolean } | null>(null);
  const columns = useMemo<ColumnDef<UserRecord>[]>(() => [
    { accessorKey: "full_name", size: 20, header: "Nama", cell: ({ row }) => <span className="font-medium">{row.original.full_name}</span> },
    { accessorKey: "email", size: 26, header: "Email", cell: ({ row }) => <span className="break-all">{row.original.email}</span> },
    { accessorKey: "role", size: 13, header: "Peran", cell: ({ row }) => roleLabels[row.original.role] },
    { accessorKey: "is_active", size: 13, header: "Status", cell: ({ row }) => (
      <Badge variant={row.original.is_active ? "secondary" : "outline"}>
        {row.original.is_active ? "Aktif" : "Nonaktif"}
      </Badge>
    ) },
    { accessorKey: "created_at", size: 18, header: "Dibuat", cell: ({ row }) => (
      <span className="whitespace-nowrap">{dateLabel(row.original.created_at)}</span>
    ) },
    { id: "actions", size: 10, header: "Tindakan", enableSorting: false, cell: ({ row }) => (
      <div className="flex justify-end gap-2">
        <Button aria-label={`Edit ${row.original.full_name}`} onClick={() => setDialog({ user: row.original })} size="icon" variant="outline">
          <Pencil aria-hidden="true" className="size-4" />
        </Button>
        {row.original.is_active && (
          <Button aria-label={`Nonaktifkan ${row.original.full_name}`} onClick={() => setDialog({ user: row.original, deleting: true })} size="icon" variant="destructive">
            <Trash2 aria-hidden="true" className="size-4" />
          </Button>
        )}
      </div>
    ) },
  ], []);
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

  const setUserDialog = (value: { user?: UserRecord; deleting?: boolean } | null) => {
    setDialog(value);
  };

  return (
    <section className="mx-auto max-w-6xl">
      <PageHeader description="Kelola akun pengguna, peran, dan status akses." title="Pengguna">
        <Button onClick={() => setUserDialog({})}>
          <Plus data-icon="inline-start" />
          Tambah pengguna
        </Button>
      </PageHeader>

      {!query.isPending && !query.error && <UsersSummary users={users} />}

      {query.error && <QueryState query={query} />}
      <form
        aria-label="Filter pengguna"
        className="mb-5 rounded-xl border border-border bg-background p-4"
        onSubmit={(event) => {
          event.preventDefault();
          setRole(draftRole);
          setActive(draftActive);
        }}
      >
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="flex flex-wrap items-end gap-3">
            <label className="grid gap-1.5 text-sm" htmlFor="users-role-filter">
              Peran
              <NativeSelect id="users-role-filter" onChange={(event) => setDraftRole(event.target.value as RoleFilter)} value={draftRole}>
                <NativeSelectOption value="all">Semua peran</NativeSelectOption>
                <NativeSelectOption value="superadmin">Superadmin</NativeSelectOption>
                <NativeSelectOption value="lecturer">Dosen</NativeSelectOption>
              </NativeSelect>
            </label>
            <label className="grid gap-1.5 text-sm" htmlFor="users-active-filter">
              Status
              <NativeSelect id="users-active-filter" onChange={(event) => setDraftActive(event.target.value as ActiveFilter)} value={draftActive}>
                <NativeSelectOption value="all">Semua status</NativeSelectOption>
                <NativeSelectOption value="true">Aktif</NativeSelectOption>
                <NativeSelectOption value="false">Nonaktif</NativeSelectOption>
              </NativeSelect>
            </label>
          </div>
          <div className="flex items-center gap-2">
            <Button onClick={() => {
              setDraftRole("all");
              setDraftActive("all");
              setRole("all");
              setActive("all");
            }} type="button" variant="outline">
              <RotateCcw aria-hidden="true" className="size-4" />
              Reset
            </Button>
            <Button type="submit">Terapkan</Button>
          </div>
        </div>
      </form>
      <DataTable
          actions={<Button aria-label="Segarkan" disabled={query.isFetching} onClick={() => void query.refetch()} type="button" variant="outline"><RefreshCw aria-hidden="true" className="size-4" /><span className="hidden sm:inline">Segarkan</span></Button>}
          columns={columns}
          data={visibleUsers}
          emptyMessage={query.isPending ? "Memuat data" : users.length ? "Tidak ada pengguna yang cocok dengan pencarian." : "Belum ada pengguna"}
          getRowId={(record) => record.id}
          search={<label className="grid w-full gap-1.5 text-sm sm:w-64" htmlFor="users-search">Cari pengguna<Input autoComplete="off" id="users-search" onChange={(event) => setSearch(event.target.value)} placeholder="Nama atau email" type="search" value={search} /></label>}
        />
      {dialog && <UserDialog {...dialog} close={() => setUserDialog(null)} />}
    </section>
  );
}
