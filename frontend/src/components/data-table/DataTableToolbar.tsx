import type { ReactNode } from "react";
interface DataTableToolbarProps {
  children?: ReactNode;
  search?: ReactNode;
  actions?: ReactNode;
  pageSize: number;
  pageSizeOptions?: number[];
  onPageSizeChange: (size: number) => void;
}

/** Kontrol pencarian, filter, jumlah baris, dan aksi tabel. */
export function DataTableToolbar({ children, search, actions, pageSize, pageSizeOptions = [10, 25, 50], onPageSizeChange }: DataTableToolbarProps) {
  return (
    <div className="flex flex-col gap-4 border-b border-border pb-4 lg:flex-row lg:items-end lg:justify-between">
      <div className="flex flex-wrap items-end gap-3">
        <label className="flex h-9 items-center gap-2 whitespace-nowrap text-sm text-muted-foreground">
          Baris per halaman
          <select aria-label="Baris per halaman" className="h-9 rounded-md border border-input bg-background px-2 text-foreground" onChange={(event) => onPageSizeChange(Number(event.target.value))} value={pageSize}>
            {pageSizeOptions.map((size) => <option key={size} value={size}>{size}</option>)}
          </select>
        </label>
        {children}
      </div>
      <div className="flex flex-wrap items-end gap-2 lg:justify-end">
        {search}
        {actions}
      </div>
    </div>
  );
}
