/**
 * Halaman audit dan retry pengiriman rilis untuk route superadmin.
 * queued menandai pengiriman menunggu; sent mencerminkan hasil transport yang dicatat worker.
 */
import { useMemo, useState } from "react";
import { Filter, RefreshCw, RotateCcw, RotateCw } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { ColumnDef } from "@tanstack/react-table";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select";
import { DataTable } from "@/components/data-table";
import { errorMessage } from "@/features/academic/api";
import { PageHeader, QueryState } from "@/features/academic/Management";
import { useAuth } from "@/features/auth/useAuth";
import api from "@/lib/api";

/**
 * Status persistence yang diterima dari API, terpisah dari label tampilan.
 */
type NotificationStatus = "queued" | "sent" | "failed";
/**
 * Catatan audit; alamat/error/sent_at bisa null sesuai tahap pengiriman.
 */
interface NotificationRecord {
  id: string;
  grade_id: string;
  student_email: string | null;
  status: NotificationStatus;
  error_message: string | null;
  sent_at: string | null;
  created_at: string;
}
/**
 * Pilihan semua status melengkapi nilai status persistence tanpa mengubah kontrak backend.
 */
type StatusFilter = "all" | NotificationStatus;

const statusLabels: Record<NotificationStatus, string> = {
  queued: "Antrean",
  sent: "Terkirim",
  failed: "Gagal",
};

/**
 * Terjemahkan status pengiriman menjadi label/badge yang konsisten pada tabel audit.
 */
function StatusBadge({ status }: { status: NotificationStatus }) {
  return (
    <Badge variant={status === "failed" ? "destructive" : status === "sent" ? "secondary" : "outline"}>
      {statusLabels[status]}
    </Badge>
  );
}

/**
 * Format waktu lokal untuk audit; nilai kosong diberi penanda agar tidak dianggap belum
 * dimuat.
 */
function dateLabel(value: string | null) {
  return value ? new Intl.DateTimeFormat("id-ID", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "—";
}

/**
 * Pisahkan cache berdasarkan pengguna/filter dan segarkan daftar setelah retry
 * administratif.
 */
export function NotificationsPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<StatusFilter>("failed");
  const [draftFilter, setDraftFilter] = useState<StatusFilter>("failed");
  const [search, setSearch] = useState("");
  const notificationsKey = ["notifications", user?.id] as const;
  const queryKey = [...notificationsKey, filter] as const;
  const query = useQuery({
    queryKey,
    queryFn: async () => (await api.get<NotificationRecord[]>("/admin/notifications", {
      params: filter === "all" ? undefined : { status: filter },
    })).data,
    enabled: Boolean(user),
    retry: false,
  });
  const retry = useMutation({
    mutationFn: async (notificationId: string) =>
      (await api.post<NotificationRecord>(`/admin/notifications/${notificationId}/retry`)).data,
    onSuccess: async (updated) => {
      queryClient.setQueryData([...notificationsKey, updated.status], [updated]);
      await queryClient.invalidateQueries({ queryKey: notificationsKey });
      setFilter(updated.status);
      setDraftFilter(updated.status);
    },
  });

  const records = query.data ?? [];
  const normalizedSearch = search.trim().toLocaleLowerCase("id-ID");
  const visibleRecords = records.filter((record) =>
    `${record.student_email ?? ""} ${record.status} ${statusLabels[record.status]} ${record.error_message ?? ""}`
      .toLocaleLowerCase("id-ID").includes(normalizedSearch),
  );
  const columns = useMemo<ColumnDef<NotificationRecord>[]>(() => [
    { accessorKey: "status", size: 12, header: "Status", cell: ({ row }) => <StatusBadge status={row.original.status} /> },
    {
      id: "student_email",
      size: 22,
      accessorFn: (row) => row.student_email ?? "",
      header: "Email mahasiswa",
      cell: ({ row }) => <span className="block min-w-0 whitespace-normal text-wrap break-all">{row.original.student_email ?? "Email tidak tersedia"}</span>,
    },
    { accessorKey: "created_at", size: 16, header: "Dibuat", cell: ({ row }) => <span className="block whitespace-normal text-wrap">{dateLabel(row.original.created_at)}</span> },
    { accessorKey: "sent_at", size: 16, header: "Terkirim", cell: ({ row }) => <span className="block whitespace-normal text-wrap">{dateLabel(row.original.sent_at)}</span> },
    { accessorKey: "error_message", size: 24, header: "Detail kegagalan", enableSorting: false, cell: ({ row }) => <span className="block min-w-0 whitespace-normal text-wrap [overflow-wrap:anywhere]">{row.original.error_message ?? "—"}</span> },
    {
      id: "actions",
      size: 10,
      header: () => <span className="sr-only">Tindakan</span>,
      enableSorting: false,
      cell: ({ row }) => row.original.status === "failed" ? (
        <Button aria-label={`Kirim ulang ke ${row.original.student_email ?? "mahasiswa"}`} disabled={retry.isPending} onClick={() => retry.mutate(row.original.id)} size="icon" type="button" variant="outline">
          <RotateCw aria-hidden="true" className="size-4" />
        </Button>
      ) : null,
    },
  ], [retry]);

  return (
    <section className="mx-auto max-w-6xl">
      <PageHeader description="Pantau status email rilis nilai dan kirim ulang pengiriman yang gagal." title="Status notifikasi" />

      {query.error && <QueryState query={query} />}
      <form
        aria-label="Filter notifikasi"
        className="mb-5 rounded-xl border border-border bg-background p-4"
        onSubmit={(event) => {
          event.preventDefault();
          setFilter(draftFilter);
        }}
      >
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <label className="grid gap-1.5 text-sm" htmlFor="notification-status-filter">
            Status
            <NativeSelect id="notification-status-filter" onChange={(event) => setDraftFilter(event.target.value as StatusFilter)} value={draftFilter}>
              <NativeSelectOption value="all">Semua status</NativeSelectOption>
              <NativeSelectOption value="queued">Antrean</NativeSelectOption>
              <NativeSelectOption value="sent">Terkirim</NativeSelectOption>
              <NativeSelectOption value="failed">Gagal</NativeSelectOption>
            </NativeSelect>
          </label>
          <div className="flex items-center gap-2">
            <Button onClick={() => {
              setDraftFilter("failed");
              setFilter("failed");
            }} type="button" variant="outline">
              <RotateCcw aria-hidden="true" className="size-4" />
              Reset
            </Button>
            <Button type="submit">
              <Filter aria-hidden="true" className="size-4" />
              Terapkan
            </Button>
          </div>
        </div>
      </form>
      <DataTable
          actions={<Button aria-label="Segarkan" disabled={query.isFetching} onClick={() => void query.refetch()} type="button" variant="outline"><RefreshCw aria-hidden="true" className="size-4" /><span className="hidden sm:inline">Segarkan</span></Button>}
          columns={columns}
          data={visibleRecords}
          emptyMessage={query.isPending ? "Memuat data" : normalizedSearch ? "Tidak ada notifikasi yang cocok dengan pencarian." : "Tidak ada notifikasi untuk status ini."}
          getRowId={(row) => row.id}
          search={<label className="flex w-full items-center gap-2 whitespace-nowrap text-sm sm:w-auto" htmlFor="notification-search">Cari<Input className="w-48 sm:w-64" id="notification-search" onChange={(event) => setSearch(event.target.value)} placeholder="Email, status, atau detail kegagalan" type="search" value={search} /></label>}
        />
      {retry.error && (
        <Alert className="mt-4" variant="destructive">
          <AlertTitle>Gagal mengirim ulang notifikasi</AlertTitle>
          <AlertDescription>{errorMessage(retry.error)}</AlertDescription>
        </Alert>
      )}
    </section>
  );
}
