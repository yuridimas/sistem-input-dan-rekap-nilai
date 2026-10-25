import { useState } from "react";
import { RefreshCw } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { errorMessage } from "@/features/academic/api";
import { PageHeader, QueryState } from "@/features/academic/Management";
import { useAuth } from "@/features/auth/useAuth";
import api from "@/lib/api";

type NotificationStatus = "queued" | "sent" | "failed";
interface NotificationRecord {
  id: string;
  grade_id: string;
  student_email: string | null;
  status: NotificationStatus;
  error_message: string | null;
  sent_at: string | null;
  created_at: string;
}
type StatusFilter = "all" | NotificationStatus;

const statusLabels: Record<NotificationStatus, string> = {
  queued: "Antrean",
  sent: "Terkirim",
  failed: "Gagal",
};

function StatusBadge({ status }: { status: NotificationStatus }) {
  return (
    <Badge variant={status === "failed" ? "destructive" : status === "sent" ? "secondary" : "outline"}>
      {statusLabels[status]}
    </Badge>
  );
}

function dateLabel(value: string | null) {
  return value ? new Intl.DateTimeFormat("id-ID", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "—";
}

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

      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
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
      </div>

      {query.isPending || query.error ? (
        <QueryState query={query} />
      ) : !records.length ? (
        <p className="rounded-md border bg-background px-4 py-10 text-center text-sm text-muted-foreground" role="status">
          Tidak ada notifikasi untuk status ini.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-xl border bg-background">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Status</TableHead>
                <TableHead>Email mahasiswa</TableHead>
                <TableHead>Dibuat</TableHead>
                <TableHead>Terkirim</TableHead>
                <TableHead>Detail kegagalan</TableHead>
                <TableHead><span className="sr-only">Tindakan</span></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {records.map((row) => (
                <TableRow key={row.id}>
                  <TableCell><StatusBadge status={row.status} /></TableCell>
                  <TableCell className="max-w-64 break-all whitespace-normal">{row.student_email ?? "Email tidak tersedia"}</TableCell>
                  <TableCell className="whitespace-nowrap">{dateLabel(row.created_at)}</TableCell>
                  <TableCell className="whitespace-nowrap">{dateLabel(row.sent_at)}</TableCell>
                  <TableCell className="max-w-sm whitespace-normal">{row.error_message ?? "—"}</TableCell>
                  <TableCell>
                    {row.status === "failed" && (
                      <Button
                        disabled={retry.isPending}
                        onClick={() => retry.mutate(row.id)}
                        type="button"
                        variant="outline"
                      >
                        {retry.isPending && retry.variables === row.id ? "Mengirim ulang…" : `Kirim ulang ke ${row.student_email ?? "mahasiswa"}`}
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
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
