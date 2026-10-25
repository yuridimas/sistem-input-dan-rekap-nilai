import axios from "axios";

import { errorMessage } from "@/features/academic/api";
import api from "@/lib/api";

export function filenameFromDisposition(
  disposition: string | undefined,
  fallback: string,
) {
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
  return filename.split(/[\\/]/).pop()?.replace(/[\r\n]/g, "") || fallback;
}

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
