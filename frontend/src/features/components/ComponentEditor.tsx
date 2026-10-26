/**
 * Editor konfigurasi lengkap untuk tab komponen halaman kelas.
 * Mempertahankan ID tersimpan agar perubahan urutan tidak memutus relasi skor.
 */
import { useState } from "react";
import { ArrowDown, ArrowUp, Plus, Trash2 } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field";
import {
  NativeSelect,
  NativeSelectOption,
} from "@/components/ui/native-select";
import {
  NoData,
  Notice,
  QueryState,
  TextField,
} from "@/features/academic/Management";
import {
  useAcademicMutation,
  useAcademicQuery,
  type GradeComponent,
} from "@/features/academic/api";
import api from "@/lib/api";

/**
 * Key lokal menjaga identitas baris baru sebelum backend memberikan ID komponen.
 */
interface ComponentDraft {
  key: string;
  id?: string;
  name: string;
  category: GradeComponent["category"];
  weight: string;
  max_score: string;
}

/**
 * Ubah konfigurasi server menjadi input teks; kelas kosong diawali UTS/UAS masing-masing
 * 50%.
 * @returns Draft baru; UUID lokal tidak dikirim sebagai ID database.
 */
function draftRows(rows: GradeComponent[]): ComponentDraft[] {
  return rows.length
    ? rows.map((row) => ({
        ...row,
        key: row.id,
        weight: String(row.weight),
        max_score: String(row.max_score),
      }))
    : [
        {
          key: crypto.randomUUID(),
          name: "UTS",
          category: "uts",
          weight: "50",
          max_score: "100",
        },
        {
          key: crypto.randomUUID(),
          name: "UAS",
          category: "uas",
          weight: "50",
          max_score: "100",
        },
      ];
}

/**
 * Parse angka nonnegatif maksimal dua desimal ke integer seperseratus tanpa jumlah float.
 * @returns Integer aman atau null untuk format/angka di luar presisi aman.
 */
function hundredths(value: string) {
  // Pola menerima desimal nonnegatif termasuk .5/5.; menolak eksponen dan lebih dari dua desimal.
  if (!/^(?:\d+(?:\.\d{0,2})?|\.\d{1,2})$/.test(value)) return null;
  const [whole, fraction = ""] = value.split(".");
  const result = Number(whole) * 100 + Number(fraction.padEnd(2, "0"));
  return Number.isSafeInteger(result) ? result : null;
}

/**
 * Simpan seluruh konfigurasi melalui PUT hanya setelah validasi UI dan pemeriksaan locked.
 */
function Editor({
  classId,
  initial,
  locked,
}: {
  classId: string;
  initial: GradeComponent[];
  locked: boolean;
}) {
  const [rows, setRows] = useState(() => draftRows(initial));
  const [saved, setSaved] = useState(false);
  const weights = rows.map((row) => hundredths(row.weight));
  const total = weights.reduce<number>((sum, weight) => sum + (weight ?? 0), 0);
  const valid =
    rows.length > 0 &&
    rows.every(
      (row, index) =>
        row.name.trim() &&
        weights[index] !== null &&
        weights[index]! > 0 &&
        weights[index]! <= 10000 &&
        (hundredths(row.max_score) ?? 0) > 0 &&
        // 999999 seperseratus = 9999.99, batas presisi max_score Numeric(6, 2).
        hundredths(row.max_score)! <= 999999,
    ) &&
    total === 10000 &&
    rows.some((row) => row.category === "uts") &&
    rows.some((row) => row.category === "uas");
  const mutation = useAcademicMutation(async () => {
    const payload = rows.map((row, order_index) => ({
      ...(row.id ? { id: row.id } : {}),
      name: row.name.trim(),
      category: row.category,
      weight: row.weight,
      max_score: row.max_score,
      order_index,
    }));
    const { data } = await api.put<GradeComponent[]>(
      `/classes/${classId}/components`,
      payload,
    );
    setRows(draftRows(data));
    setSaved(true);
  });
  /**
   * Terapkan edit satu draft baris dan hapus status sukses/error dari percobaan sebelumnya.
   */
  function update(index: number, values: Partial<ComponentDraft>) {
    setSaved(false);
    mutation.reset();
    setRows(rows.map((row, i) => (i === index ? { ...row, ...values } : row)));
  }
  /**
   * Tukar baris dengan tetangga sambil mempertahankan key/ID komponen.
   * direction diasumsikan -1 atau 1; tombol pemanggil menjaga index tujuan tetap valid.
   */
  function move(index: number, direction: number) {
    const next = [...rows];
    [next[index], next[index + direction]] = [
      next[index + direction],
      next[index],
    ];
    setRows(next);
    setSaved(false);
  }
  return (
    <form
      className="flex flex-col gap-5"
      onSubmit={(event) => {
        event.preventDefault();
        if (valid && !locked) mutation.mutate();
      }}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-semibold">Komponen penilaian</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Atur bobot total 100% dengan minimal satu UTS dan satu UAS.
          </p>
        </div>
        <Badge variant={valid ? "secondary" : "outline"}>
          Total bobot:{" "}
          {(total / 100).toLocaleString("id-ID", { maximumFractionDigits: 2 })}%
        </Badge>
      </div>
      <Notice error={mutation.error} />
      {saved && (
        <p className="text-sm text-muted-foreground" role="status">
          Konfigurasi komponen berhasil disimpan.
        </p>
      )}
      {!valid && !locked && (
        <Alert>
          <AlertTitle>Konfigurasi belum lengkap</AlertTitle>
          <AlertDescription>
            Isi nama, bobot dan nilai maksimum positif (maksimal dua desimal),
            sertakan UTS dan UAS, lalu pastikan bobot tepat 100%.
          </AlertDescription>
        </Alert>
      )}
      <fieldset
        className="flex min-w-0 flex-col gap-4"
        disabled={locked || mutation.isPending}
      >
        {/* Reordered rows need normal containment to retain their layout in Chromium. */}
        {rows.map((row, index) => (
          <fieldset
            className="min-w-0 rounded-xl border bg-background p-4 sm:p-5"
            key={row.key}
          >
            <legend className="px-1 text-sm font-medium">
              Komponen {index + 1}
            </legend>
            <FieldGroup style={{ containerType: "normal" }}>
              <div className="grid min-w-0 gap-4 sm:grid-cols-2">
                <TextField
                  label={`Nama komponen ${index + 1}`}
                  maxLength={100}
                  onChange={(event) =>
                    update(index, { name: event.target.value })
                  }
                  required
                  value={row.name}
                />
                <Field>
                  <FieldLabel htmlFor={`category-${row.key}`}>
                    Kategori komponen {index + 1}
                  </FieldLabel>
                  <NativeSelect
                    className="w-full"
                    id={`category-${row.key}`}
                    onChange={(event) =>
                      update(index, {
                        category: event.target
                          .value as GradeComponent["category"],
                      })
                    }
                    value={row.category}
                  >
                    <NativeSelectOption value="tugas">Tugas</NativeSelectOption>
                    <NativeSelectOption value="uts">UTS</NativeSelectOption>
                    <NativeSelectOption value="uas">UAS</NativeSelectOption>
                    <NativeSelectOption value="custom">
                      Kustom
                    </NativeSelectOption>
                  </NativeSelect>
                </Field>
                <TextField
                  label={`Bobot komponen ${index + 1} (%)`}
                  max={100}
                  min={0.01}
                  onChange={(event) =>
                    update(index, { weight: event.target.value })
                  }
                  required
                  step="0.01"
                  type="number"
                  value={row.weight}
                />
                <TextField
                  label={`Nilai maksimum komponen ${index + 1}`}
                  max={9999.99}
                  min={0.01}
                  onChange={(event) =>
                    update(index, { max_score: event.target.value })
                  }
                  required
                  step="0.01"
                  type="number"
                  value={row.max_score}
                />
              </div>
              <div className="flex flex-wrap gap-2">
                <Button
                  aria-label={`Naikkan komponen ${index + 1}`}
                  disabled={index === 0}
                  onClick={() => move(index, -1)}
                  size="sm"
                  type="button"
                  variant="outline"
                >
                  <ArrowUp data-icon="inline-start" />
                  Naik
                </Button>
                <Button
                  aria-label={`Turunkan komponen ${index + 1}`}
                  disabled={index === rows.length - 1}
                  onClick={() => move(index, 1)}
                  size="sm"
                  type="button"
                  variant="outline"
                >
                  <ArrowDown data-icon="inline-start" />
                  Turun
                </Button>
                <Button
                  aria-label={`Hapus komponen ${index + 1}`}
                  onClick={() => {
                    setRows(rows.filter((_, i) => i !== index));
                    setSaved(false);
                  }}
                  size="sm"
                  type="button"
                  variant="destructive"
                >
                  <Trash2 data-icon="inline-start" />
                  Hapus
                </Button>
              </div>
            </FieldGroup>
          </fieldset>
        ))}
        <div>
          <Button
            onClick={() => {
              setRows([
                ...rows,
                {
                  key: crypto.randomUUID(),
                  name: "",
                  category: "tugas",
                  weight: "",
                  max_score: "100",
                },
              ]);
              setSaved(false);
            }}
            type="button"
            variant="outline"
          >
            <Plus data-icon="inline-start" />
            Tambah komponen
          </Button>
        </div>
      </fieldset>
      {!locked && (
        <div className="flex flex-wrap justify-end gap-2">
          <Button
            disabled={mutation.isPending}
            onClick={() => {
              setRows(draftRows(initial));
              setSaved(false);
              mutation.reset();
            }}
            type="button"
            variant="outline"
          >
            Batal
          </Button>
          <Button disabled={!valid || mutation.isPending} type="submit">
            {mutation.isPending ? "Menyimpan…" : "Simpan komponen"}
          </Button>
        </div>
      )}
    </form>
  );
}

/**
 * Muat konfigurasi sebelum memasang editor; locked menonaktifkan mutasi kelas final.
 */
export function ComponentEditor({
  classId,
  locked,
}: {
  classId: string;
  locked: boolean;
}) {
  const query = useAcademicQuery<GradeComponent[]>(
    `/classes/${classId}/components`,
  );
  if (query.isPending || query.error) return <QueryState query={query} />;
  if (locked && !query.data?.length)
    return (
      <NoData description="Belum ada komponen tersimpan untuk kelas yang terkunci ini." />
    );
  return (
    <Editor
      classId={classId}
      initial={query.data!}
      key={`${classId}-${locked}`}
      locked={locked}
    />
  );
}
