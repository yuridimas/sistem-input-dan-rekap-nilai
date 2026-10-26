/**
 * Utilitas unduhan laporan terautentikasi yang dipakai tombol PDF/XLSX.
 * Respons blob dan error JSON memerlukan penanganan berbeda dari request data biasa.
 */
import axios from "axios";

import { errorMessage } from "@/features/academic/api";
import api from "@/lib/api";

/**
 * Pilih nama UTF-8 dari header lalu hilangkan path dan newline.
 * @param disposition Header opsional; fallback nama lokal ketika header kosong/rusak.
 * @returns Nama file tanpa direktori; decoding rusak mencoba nama reguler lalu fallback.
 */
export function filenameFromDisposition(
  disposition: string | undefined,
  fallback: string,
) {
  // filename* menangani UTF-8; filename biasa untuk server dengan header sederhana.
  const extended = disposition?.match(/filename\*=UTF-8''([^;]+)/i)?.[1];
  const regular = disposition?.match(/filename="?([^";]+)"?/i)?.[1];
  let filename = fallback;
  if (extended) {
    try {
      filename = decodeURIComponent(extended.trim());
    } catch {
      filename = regular?.trim() ?? fallback;
    }
  } else if (regular) {
    filename = regular.trim();
  }
  // Kedua pemisah path dibuang; CR/LF header tidak dibawa ke nama unduhan.
  return filename.split(/[\\/]/).pop()?.replace(/[\r\n]/g, "") || fallback;
}

/**
 * Ambil blob lewat client sesi lalu picu unduhan browser dan lepaskan object URL.
 * @param path Endpoint laporan; fallbackName nama bila server tidak memberi header.
 * @returns Promise<void>; kegagalan HTTP diteruskan ke tombol untuk ditampilkan.
 */
export async function downloadReport(path: string, fallbackName: string) {
  const response = await api.get<Blob>(path, { responseType: "blob" });
  const disposition = response.headers["content-disposition"] as string | undefined;
  const filename = filenameFromDisposition(disposition, fallbackName);
  const objectUrl = URL.createObjectURL(response.data);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = filename;
  link.style.display = "none";
  document.body.append(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 0);
}

/**
 * Baca pesan detail JSON yang diterima sebagai Blob pada kegagalan unduhan.
 * @returns Promise<string>; body non-JSON memakai pesan error API bersama.
 */
export async function reportErrorMessage(error: unknown) {
  if (axios.isAxiosError(error) && error.response?.data instanceof Blob) {
    try {
      const body: unknown = JSON.parse(await error.response.data.text());
      if (body && typeof body === "object" && "detail" in body) {
        const detail = body.detail;
        if (typeof detail === "string") return detail;
      }
    } catch {
      // Fall back to the shared API error message when the body is not JSON.
    }
  }
  return errorMessage(error);
}
