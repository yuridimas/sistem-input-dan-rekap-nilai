import type { Table as TanStackTable } from "@tanstack/react-table";

import { Button } from "@/components/ui/button";

interface DataTablePaginationProps<TData> {
  table: TanStackTable<TData>;
}

/** Kontrol aksesibel untuk jumlah baris dan perpindahan halaman DataTable. */
export function DataTablePagination<TData>({
  table,
}: DataTablePaginationProps<TData>) {
  const { pageIndex, pageSize } = table.getState().pagination;
  const rowCount = table.getFilteredRowModel().rows.length;
  const start = rowCount === 0 ? 0 : pageIndex * pageSize + 1;
  const end = Math.min((pageIndex + 1) * pageSize, rowCount);

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
      <p aria-live="polite" className="text-muted-foreground">
        {start}–{end} dari {rowCount} baris
      </p>
      <div className="flex items-center gap-2">
        <span aria-live="polite" className="min-w-24 text-center text-muted-foreground">
          Halaman {pageIndex + 1} dari {Math.max(table.getPageCount(), 1)}
        </span>
        <Button aria-label="Halaman sebelumnya" disabled={!table.getCanPreviousPage()} onClick={() => table.previousPage()} variant="outline">
          Sebelumnya
        </Button>
        <Button aria-label="Halaman berikutnya" disabled={!table.getCanNextPage()} onClick={() => table.nextPage()} variant="outline">
          Berikutnya
        </Button>
      </div>
    </div>
  );
}
