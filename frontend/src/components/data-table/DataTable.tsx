import {
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type SortingState,
} from "@tanstack/react-table";
import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import { DataTablePagination } from "./DataTablePagination";

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
  emptyMessage?: string;
  filterValue?: string;
  getRowId?: (row: TData, index: number) => string;
  initialPageSize?: number;
}

/** Render tabel data dengan sorting, pencarian global opsional, dan pagination lokal. */
export function DataTable<TData, TValue>({
  columns,
  data,
  emptyMessage = "Tidak ada data",
  filterValue = "",
  getRowId,
  initialPageSize = 10,
}: DataTableProps<TData, TValue>) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const table = useReactTable({
    data,
    columns,
    getRowId,
    state: { sorting, globalFilter: filterValue },
    onSortingChange: setSorting,
    globalFilterFn: "includesString",
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageIndex: 0, pageSize: initialPageSize } },
  });

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto rounded-xl border border-border bg-background">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  const sorted = header.column.getIsSorted();
                  const label = typeof header.column.columnDef.header === "string"
                    ? header.column.columnDef.header
                    : header.column.id;
                  return (
                    <TableHead
                      aria-sort={sorted === "asc" ? "ascending" : sorted === "desc" ? "descending" : "none"}
                      key={header.id}
                    >
                      {header.isPlaceholder ? null : header.column.getCanSort() ? (
                        <Button
                          aria-label={label}
                          className="-ml-2"
                          onClick={header.column.getToggleSortingHandler()}
                          variant="ghost"
                        >
                          {flexRender(header.column.columnDef.header, header.getContext())}
                          {sorted === "asc" ? <ArrowUp aria-hidden="true" /> : sorted === "desc" ? <ArrowDown aria-hidden="true" /> : <ArrowUpDown aria-hidden="true" />}
                        </Button>
                      ) : flexRender(header.column.columnDef.header, header.getContext())}
                    </TableHead>
                  );
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.length ? table.getRowModel().rows.map((row) => (
              <TableRow key={row.id}>
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</TableCell>
                ))}
              </TableRow>
            )) : (
              <TableRow>
                <TableCell className="h-24 text-center" colSpan={table.getVisibleLeafColumns().length}>
                  <span role="status">{emptyMessage}</span>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      <DataTablePagination table={table} />
    </div>
  );
}
