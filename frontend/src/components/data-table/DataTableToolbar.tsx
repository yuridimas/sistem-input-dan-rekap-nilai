import type { ReactNode } from "react";

interface DataTableToolbarProps {
  children?: ReactNode;
  actions?: ReactNode;
}

/** Slot kontrol halaman untuk pencarian/filter dan aksi khusus domain. */
export function DataTableToolbar({ children, actions }: DataTableToolbarProps) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3">
      <div className="flex flex-wrap items-end gap-3">{children}</div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}
