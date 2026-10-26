/**
 * Komponen pengelolaan bersama bagi form dan halaman fitur akademik.
 * Menyatukan state loading/error, dialog mutasi, serta hubungan label/pesan validasi.
 */
import {
  useId,
  type ComponentProps,
  type FormEvent,
  type ReactNode,
} from "react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty";
import { Field, FieldError, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { errorMessage } from "./api";

/**
 * Satukan judul/deskripsi halaman dengan slot tindakan tanpa mengikatnya pada resource
 * tertentu.
 */
export function PageHeader({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children?: ReactNode;
}) {
  return (
    <div className="mb-7 flex flex-wrap items-start justify-between gap-4">
      <div className="min-w-0">
        <h1 className="break-words text-2xl font-semibold tracking-tight">
          {title}
        </h1>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">
          {description}
        </p>
      </div>
      {children}
    </div>
  );
}

/**
 * Tampilkan pesan error API bersama; error kosong menghasilkan null.
 */
export function Notice({ error }: { error: unknown }) {
  return error ? (
    <Alert variant="destructive" role="alert">
      <AlertTitle>Tindakan belum berhasil</AlertTitle>
      <AlertDescription>{errorMessage(error)}</AlertDescription>
    </Alert>
  ) : null;
}

/**
 * Bedakan loading dan error query dengan tombol refetch; kondisi sukses menghasilkan null.
 */
export function QueryState({
  query,
}: {
  query: {
    isPending: boolean;
    error: unknown;
    refetch: () => unknown;
    isFetching: boolean;
  };
}) {
  if (query.isPending)
    return (
      <div className="flex flex-col gap-3" role="status">
        <span className="sr-only">Memuat data…</span>
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-24 w-full" />
      </div>
    );
  if (query.error)
    return (
      <div className="flex flex-col items-start gap-4">
        <Notice error={query.error} />
        <Button
          disabled={query.isFetching}
          onClick={() => void query.refetch()}
          variant="outline"
        >
          Coba lagi
        </Button>
      </div>
    );
  return null;
}

/**
 * Jelaskan kondisi kosong menggunakan judul opsional dan deskripsi yang ditentukan
 * halaman.
 */
export function NoData({
  title = "Belum ada data",
  description,
}: {
  title?: string;
  description: string;
}) {
  return (
    <Empty className="border bg-background py-12">
      <EmptyHeader>
        <EmptyTitle>{title}</EmptyTitle>
        <EmptyDescription>{description}</EmptyDescription>
      </EmptyHeader>
    </Empty>
  );
}

/**
 * Hubungkan label, input, dan error lewat ID unik agar validasi dapat dibaca screen
 * reader.
 */
export function TextField({
  label,
  error,
  ...props
}: ComponentProps<typeof Input> & { label: string; error?: string }) {
  const id = useId();
  return (
    <Field data-invalid={Boolean(error)}>
      <FieldLabel htmlFor={id}>{label}</FieldLabel>
      <Input
        {...props}
        aria-describedby={error ? `${id}-error` : undefined}
        aria-invalid={Boolean(error)}
        id={id}
      />
      <FieldError id={`${id}-error`}>{error}</FieldError>
    </Field>
  );
}

/**
 * Cegah penutupan/edit selama mutasi agar hasil request tidak kehilangan konteks form.
 */
export function MutationDialog({
  title,
  description,
  children,
  close,
  busy,
  error,
  onSubmit,
  submitLabel = "Simpan",
  destructive = false,
  submitDisabled = false,
}: {
  title: string;
  description: string;
  children?: ReactNode;
  close: () => void;
  busy: boolean;
  error: unknown;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  submitLabel?: string;
  destructive?: boolean;
  submitDisabled?: boolean;
}) {
  return (
    <Dialog
      open
      onOpenChange={(open) => {
        if (!open && !busy) close();
      }}
    >
      <DialogContent
        className="max-h-[85dvh] overflow-y-auto sm:max-w-lg"
        showCloseButton={!busy}
      >
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <form className="flex min-w-0 flex-col gap-5" onSubmit={onSubmit}>
          <fieldset className="flex min-w-0 flex-col gap-5" disabled={busy}>
            {children}
          </fieldset>
          <Notice error={error} />
          <DialogFooter>
            <Button
              disabled={busy}
              onClick={close}
              type="button"
              variant="outline"
            >
              Batal
            </Button>
            <Button
              disabled={busy || submitDisabled}
              type="submit"
              variant={destructive ? "destructive" : "default"}
            >
              {busy ? "Memproses…" : submitLabel}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
