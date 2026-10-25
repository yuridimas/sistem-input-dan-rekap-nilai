import { useState } from "react";
import { Link } from "react-router-dom";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { NoData, QueryState } from "@/features/academic/Management";
import { cellChanged, cellKey } from "./draft";
import { configurationValid, missingCells, type GradeEntry } from "./hooks";

const inputId = (enrollment: string, component: string) =>
  `score-${enrollment}-${component}`;

export function GradeEntryGrid({ entry }: { entry: GradeEntry }) {
  const [reloadOpen, setReloadOpen] = useState(false);
  const { engine, snapshot, query } = entry;
  const data = snapshot.data;
  if (!data || query.error) return <QueryState query={query} />;
  const validConfig = configurationValid(data);
  const dirty = engine.hasChanges();
  const anyFinal = data.grades.some((row) => row.status === "finalized");
  const allFinal =
    data.grades.length > 0 &&
    data.grades.every((row) => row.status === "finalized");
  const missing = missingCells(data);
  const missingList = missing.length
    ? missing
    : entry.serverMissing.map((item) => ({
        ...item,
        enrollment:
          data.grades.find((row) => row.student.nim === item.student_nim)
            ?.enrollment_id ?? "",
        component:
          data.components.find((row) => row.name === item.component_name)?.id ??
          "",
      }));
  function focusMissing(enrollment: string, component: string) {
    entry.closeDialog();
    window.setTimeout(
      () => document.getElementById(inputId(enrollment, component))?.focus(),
      50,
    );
  }
  return (
    <section
      aria-labelledby="grade-entry-title"
      className="flex min-w-0 flex-col gap-5"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-semibold" id="grade-entry-title">
            Input nilai mahasiswa
          </h2>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">
            Nilai disimpan saat keluar dari sel. Skor kosong berkontribusi nol
            pada nilai akhir draft; isi angka 0 bila memang bernilai nol.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            disabled={
              !dirty || snapshot.frozen || snapshot.paused || snapshot.saving
            }
            onClick={() => void engine.flush()}
            variant="outline"
          >
            Simpan semua
          </Button>
          <Button
            disabled={
              snapshot.frozen ||
              snapshot.paused ||
              anyFinal ||
              !validConfig ||
              !data.grades.length ||
              entry.preparing ||
              entry.finalizing
            }
            onClick={() => void entry.prepare()}
          >
            {entry.preparing ? "Memeriksa nilai…" : "Finalisasi & Rilis"}
          </Button>
        </div>
      </div>
      <p className="text-sm text-muted-foreground" role="status">
        {snapshot.saving
          ? "Menyimpan perubahan…"
          : snapshot.error
            ? "Ada perubahan yang gagal disimpan. Gunakan Simpan semua untuk mencoba lagi."
            : dirty
              ? "Ada perubahan belum tersimpan."
              : "Semua perubahan tersimpan."}
      </p>
      {(entry.actionError || snapshot.error || snapshot.warning) && (
        <Alert
          variant={
            entry.actionError || snapshot.error ? "destructive" : "default"
          }
        >
          <AlertTitle>Periksa status nilai</AlertTitle>
          <AlertDescription>
            {entry.actionError || snapshot.error || snapshot.warning}
          </AlertDescription>
        </Alert>
      )}
      {entry.notice && (
        <Alert>
          <AlertTitle>Status rilis</AlertTitle>
          <AlertDescription>{entry.notice}</AlertDescription>
        </Alert>
      )}
      {entry.uncertain && (
        <div>
          <Button
            disabled={entry.preparing}
            onClick={() => void entry.checkRelease()}
            variant="outline"
          >
            Periksa status rilis
          </Button>
        </div>
      )}
      {snapshot.paused && (
        <div>
          <Button
            disabled={snapshot.saving}
            onClick={() => setReloadOpen(true)}
            variant="outline"
          >
            Muat ulang nilai
          </Button>
        </div>
      )}
      {anyFinal && (
        <Alert>
          <AlertTitle>
            {allFinal
              ? "Nilai kelas sudah dirilis"
              : "Kelas memiliki nilai final"}
          </AlertTitle>
          <AlertDescription>
            {allFinal
              ? "Seluruh nilai mahasiswa bersifat baca saja dan tidak dapat diubah."
              : "Nilai draft masih dapat disimpan. Finalisasi ulang kelas tidak tersedia karena sudah ada nilai final."}
          </AlertDescription>
        </Alert>
      )}
      {!validConfig ? (
        <Alert>
          <AlertTitle>Komponen penilaian belum siap</AlertTitle>
          <AlertDescription>
            Lengkapi komponen dengan bobot 100%, minimal satu UTS dan satu UAS
            melalui{" "}
            <Link className="underline" to="?tab=components">
              tab Komponen Penilaian
            </Link>
            .
          </AlertDescription>
        </Alert>
      ) : !data.grades.length ? (
        <NoData description="Daftarkan mahasiswa melalui tab Mahasiswa sebelum mengisi nilai." />
      ) : (
        <div className="overflow-hidden rounded-xl border bg-background">
          <Table aria-label="Grid nilai mahasiswa">
            <TableHeader>
              <TableRow>
                <TableHead className="min-w-44">Mahasiswa</TableHead>
                {data.components.map((component) => (
                  <TableHead
                    className="min-w-40 whitespace-normal"
                    key={component.id}
                  >
                    <span className="block">{component.name}</span>
                    <span className="mt-1 block text-xs font-normal text-muted-foreground">
                      Bobot {component.weight}% · Maks. {component.max_score}
                    </span>
                  </TableHead>
                ))}
                <TableHead className="min-w-32">Nilai akhir</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.grades.map((row) => {
                const rowDirty = data.components.some((component) => {
                  const cell =
                    snapshot.cells[cellKey(row.enrollment_id, component.id)];
                  return cell && cellChanged(cell);
                });
                return (
                  <TableRow key={row.enrollment_id}>
                    <TableCell className="max-w-60 whitespace-normal align-top">
                      <p className="font-medium">{row.student.full_name}</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {row.student.nim}
                      </p>
                    </TableCell>
                    {data.components.map((component) => {
                      const cell =
                        snapshot.cells[
                          cellKey(row.enrollment_id, component.id)
                        ];
                      const id = inputId(row.enrollment_id, component.id);
                      return (
                        <TableCell className="align-top" key={component.id}>
                          <Input
                            aria-describedby={`${id}-status`}
                            aria-invalid={Boolean(cell.error || cell.failure)}
                            aria-label={`${row.student.nim} ${row.student.full_name} — ${component.name}`}
                            autoComplete="off"
                            className="min-w-24 tabular-nums"
                            disabled={
                              row.status === "finalized" ||
                              snapshot.frozen ||
                              snapshot.paused
                            }
                            id={id}
                            inputMode="decimal"
                            onBlur={() => void engine.queue(row.enrollment_id)}
                            onChange={(event) =>
                              engine.edit(
                                row.enrollment_id,
                                component.id,
                                event.target.value,
                              )
                            }
                            type="text"
                            value={cell.value}
                          />
                          <p
                            className="mt-1 max-w-48 whitespace-normal text-xs text-muted-foreground"
                            id={`${id}-status`}
                          >
                            {cell.error ??
                              (cell.failure
                                ? "Gagal disimpan"
                                : cellChanged(cell)
                                  ? "Belum tersimpan"
                                  : cell.saved === ""
                                    ? "Belum dinilai"
                                    : "Tersimpan")}
                          </p>
                        </TableCell>
                      );
                    })}
                    <TableCell className="align-top tabular-nums">
                      <p>
                        {row.final_score === null
                          ? "—"
                          : Number(row.final_score).toLocaleString("id-ID", {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2,
                            })}
                      </p>
                      {rowDirty && (
                        <p className="mt-1 max-w-32 whitespace-normal text-xs text-muted-foreground">
                          Belum mengikuti perubahan terbaru
                        </p>
                      )}
                    </TableCell>
                    <TableCell className="align-top">
                      <Badge
                        variant={
                          row.status === "finalized" ? "default" : "secondary"
                        }
                      >
                        {row.status === "finalized" ? "Finalized" : "Draft"}
                      </Badge>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      )}

      <Dialog
        open={entry.dialogOpen}
        onOpenChange={(open) => {
          if (!open) entry.closeDialog();
        }}
      >
        <DialogContent
          className="max-h-[85dvh] overflow-y-auto sm:max-w-lg"
          showCloseButton={!entry.finalizing}
        >
          <DialogHeader>
            <DialogTitle>Finalisasi &amp; Rilis Nilai</DialogTitle>
            <DialogDescription>
              {data.grades.length} mahasiswa akan dirilis. Nilai final tidak
              dapat diedit dan notifikasi mahasiswa akan diantrekan.
            </DialogDescription>
          </DialogHeader>
          {entry.actionError && (
            <p className="text-sm text-destructive" role="alert">
              {entry.actionError}
            </p>
          )}
          {missingList.length ? (
            <div>
              <p className="mb-3 text-sm font-medium">
                {missingList.length} skor komponen belum lengkap:
              </p>
              <ul className="flex max-h-64 flex-col gap-2 overflow-y-auto">
                {missingList.map((item, index) => (
                  <li
                    key={`${item.student_nim}-${item.component_name}-${index}`}
                  >
                    <Button
                      disabled={entry.finalizing}
                      onClick={() =>
                        focusMissing(item.enrollment, item.component)
                      }
                      variant="link"
                    >
                      {item.student_nim} — {item.component_name}
                    </Button>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="text-sm">Seluruh skor komponen sudah lengkap.</p>
          )}
          <DialogFooter>
            <Button
              disabled={entry.finalizing}
              onClick={entry.closeDialog}
              variant="outline"
            >
              Batal
            </Button>
            <Button
              disabled={
                entry.finalizing ||
                missingList.length > 0 ||
                !validConfig ||
                anyFinal ||
                dirty
              }
              onClick={() => void entry.confirm()}
            >
              {entry.finalizing ? "Merilis nilai…" : "Konfirmasi rilis"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <Dialog open={reloadOpen} onOpenChange={setReloadOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Muat ulang nilai?</DialogTitle>
            <DialogDescription>
              Perubahan lokal yang belum tersimpan akan dibuang setelah data
              terbaru berhasil dimuat.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button onClick={() => setReloadOpen(false)} variant="outline">
              Batal
            </Button>
            <Button
              disabled={query.isFetching}
              onClick={async () => {
                if (await entry.reload()) setReloadOpen(false);
              }}
              variant="destructive"
            >
              Buang draft dan muat ulang
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </section>
  );
}
