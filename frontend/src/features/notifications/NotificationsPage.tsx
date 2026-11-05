/**
 * Halaman audit dan retry pengiriman rilis untuk route superadmin.
 * queued menandai pengiriman menunggu; sent mencerminkan hasil transport yang dicatat worker.
 */
import { useMemo, useState } from "react";
import { RefreshCw } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { ColumnDef } from "@tanstack/react-table";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select";
import { DataTable, DataTableToolbar } from "@/components/data-table";
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
    },
  });

  const records = query.data ?? [];
  const columns = useMemo<ColumnDef<NotificationRecord>[]>(() => [
    { accessorKey: "status", header: "Status", cell: ({ row }) => <StatusBadge status={row.original.status} /> },
    {
      id: "student_email",
      accessorFn: (row) => row.student_email ?? "",
      header: "Email mahasiswa",
      cell: ({ row }) => <span className="max-w-64 break-all whitespace-normal">{row.original.student_email ?? "Email tidak tersedia"}</span>,
    },
    { accessorKey: "created_at", header: "Dibuat", cell: ({ row }) => <span className="whitespace-nowrap">{dateLabel(row.original.created_at)}</span> },
    { accessorKey: "sent_at", header: "Terkirim", cell: ({ row }) => <span className="whitespace-nowrap">{dateLabel(row.original.sent_at)}</span> },
    { accessorKey: "error_message", header: "Detail kegagalan", enableSorting: false, cell: ({ row }) => <span className="max-w-sm whitespace-normal">{row.original.error_message ?? "—"}</span> },
    {
      id: "actions",
      header: () => <span className="sr-only">Tindakan</span>,
      enableSorting: false,
      cell: ({ row }) => row.original.status === "failed" ? (
        <Button
          disabled={retry.isPending}
          onClick={() => retry.mutate(row.original.id)}
          type="button"
          variant="outline"
        >
          {retry.isPending && retry.variables === row.original.id ? "Mengirim ulang…" : `Kirim ulang ke ${row.original.student_email ?? "mahasiswa"}`}
        </Button>
      ) : null,
    },
  ], [retry]);

  return (
    <section className="mx-auto max-w-6xl">
      <PageHeader
        description="Pantau status email rilis nilai dan kirim ulang pengiriman yang gagal."
        title="Status notifikasi"
      >
        <Button disabled={query.isFetching} onClick={() => void query.refetch()} type="button" variant="outline">
          <RefreshCw aria-hidden="true" className="size-4" />
          Segarkan
        </Button>
      </PageHeader>

      <DataTableToolbar>
        <p className="text-sm text-muted-foreground">{records.length} notifikasi</p>
        <label className="flex items-center gap-2 text-sm" htmlFor="notification-status-filter">
          Status
          <NativeSelect id="notification-status-filter" onChange={(event) => setFilter(event.target.value as StatusFilter)} value={filter}>
            <NativeSelectOption value="all">Semua status</NativeSelectOption>
            <NativeSelectOption value="queued">Antrean</NativeSelectOption>
            <NativeSelectOption value="sent">Terkirim</NativeSelectOption>
            <NativeSelectOption value="failed">Gagal</NativeSelectOption>
          </NativeSelect>
        </label>
      </DataTableToolbar>

      {query.isPending || query.error ? (
        <QueryState query={query} />
      ) : !records.length ? (
        <p className="rounded-md border bg-background px-4 py-10 text-center text-sm text-muted-foreground" role="status">
          Tidak ada notifikasi untuk status ini.
        </p>
      ) : (
        <DataTable columns={columns} data={records} getRowId={(row) => row.id} />
      )}
      {retry.error && (
        <Alert className="mt-4" variant="destructive">
          <AlertTitle>Gagal mengirim ulang notifikasi</AlertTitle>
          <AlertDescription>{errorMessage(retry.error)}</AlertDescription>
        </Alert>
      )}
    </section>
  );
}
