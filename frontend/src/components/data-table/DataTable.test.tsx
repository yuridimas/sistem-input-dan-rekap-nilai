import { fireEvent, render, screen, within } from "@testing-library/react";
import { useState } from "react";
import { createColumnHelper } from "@tanstack/react-table";
import { describe, expect, it } from "vitest";

import { DataTable } from "./DataTable";
import { DataTableToolbar } from "./DataTableToolbar";

interface Person {
  id: string;
  name: string;
}

const rows: Person[] = [
  { id: "p-1", name: "Budi" },
  { id: "p-2", name: "Ani" },
  { id: "p-3", name: "Citra" },
];

const column = createColumnHelper<Person>();
const columns = [column.accessor("name", { header: "Nama" })];

describe("DataTable", () => {
  it("sorts a column when its header is activated", () => {
    render(<DataTable columns={columns} data={rows} getRowId={(row) => row.id} />);

    fireEvent.click(screen.getByRole("button", { name: "Nama" }));

    const renderedRows = screen.getAllByRole("row").slice(1);
    expect(renderedRows.map((row) => within(row).getByRole("cell").textContent)).toEqual([
      "Ani",
      "Budi",
      "Citra",
    ]);
  });

  it("filters rows through a caller toolbar and paginates the filtered result", () => {
    function Harness() {
      const [filter, setFilter] = useState("");
      return (
        <>
          <DataTableToolbar>
            <label>
              Cari nama
              <input aria-label="Cari nama" onChange={(event) => setFilter(event.target.value)} value={filter} />
            </label>
          </DataTableToolbar>
          <DataTable
            columns={columns}
            data={rows}
            filterValue={filter}
            getRowId={(row) => row.id}
            initialPageSize={1}
          />
        </>
      );
    }

    render(<Harness />);
    expect(screen.getByRole("cell", { name: "Budi" })).toBeInTheDocument();
    fireEvent.change(screen.getByRole("textbox", { name: "Cari nama" }), { target: { value: "i" } });
    expect(screen.getByRole("cell", { name: "Budi" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Halaman berikutnya" }));
    expect(screen.getByRole("cell", { name: "Ani" })).toBeInTheDocument();
    expect(screen.queryByRole("cell", { name: "Citra" })).not.toBeInTheDocument();
  });

  it("shows an empty message when there are no matching rows", () => {
    render(<DataTable columns={columns} data={[]} emptyMessage="Tidak ada data" />);

    expect(screen.getByRole("status")).toHaveTextContent("Tidak ada data");
  });

  it("moves between pages and disables navigation at either boundary", () => {
    function Harness() {
      return <DataTable columns={columns} data={rows} getRowId={(row) => row.id} initialPageSize={1} />;
    }

    render(<Harness />);
    expect(screen.getByRole("cell", { name: "Budi" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Halaman sebelumnya" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Halaman berikutnya" }));
    expect(screen.getByRole("cell", { name: "Ani" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Halaman sebelumnya" }));
    expect(screen.getByRole("cell", { name: "Budi" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Halaman sebelumnya" })).toBeDisabled();
  });
});
