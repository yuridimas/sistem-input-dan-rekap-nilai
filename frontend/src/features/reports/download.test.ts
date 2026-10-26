/**
 * Unit test unduhan laporan dengan Blob dan API/DOM yang dikendalikan test.
 * Tidak mengunduh file nyata; kontrak filename, cleanup object URL, dan error Blob diperiksa.
 */
import { waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import api from "@/lib/api";
import { downloadReport, filenameFromDisposition, reportErrorMessage } from "./download";

vi.mock("@/lib/api", () => ({ default: { get: vi.fn() } }));

describe("report downloads", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("uses the server filename and releases the temporary object URL", async () => {
    const blob = new Blob(["report"]);
    vi.mocked(api.get).mockResolvedValue({
      data: blob,
      headers: { "content-disposition": 'attachment; filename="nilai.pdf"' },
    });
    const createUrl = vi.fn(() => "blob:report");
    const revokeUrl = vi.fn();
    let downloadedFilename = "";
    Object.defineProperty(URL, "createObjectURL", { configurable: true, value: createUrl });
    Object.defineProperty(URL, "revokeObjectURL", { configurable: true, value: revokeUrl });
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function (this: HTMLAnchorElement) {
      downloadedFilename = this.download;
    });

    await downloadReport("/reports/student/e1/pdf", "nilai-cadangan.pdf");

    expect(api.get).toHaveBeenCalledWith("/reports/student/e1/pdf", { responseType: "blob" });
    expect(createUrl).toHaveBeenCalledWith(blob);
    expect(click).toHaveBeenCalledOnce();
    expect(downloadedFilename).toBe("nilai.pdf");
    await waitFor(() => expect(revokeUrl).toHaveBeenCalledWith("blob:report"));
  });

  it("uses the fallback name when the response has no attachment filename", () => {
    expect(filenameFromDisposition(undefined, "rekap.xlsx")).toBe("rekap.xlsx");
  });

  it("supports UTF-8 filenames from Content-Disposition", () => {
    expect(filenameFromDisposition("attachment; filename*=UTF-8''rekap%20kelas.xlsx", "fallback.xlsx"))
      .toBe("rekap kelas.xlsx");
  });

  it("reads useful error details from a Blob response", async () => {
    const error = {
      isAxiosError: true,
      response: { data: new Blob(['{"detail":"Kelas belum memiliki nilai final"}']) },
    };
    await expect(reportErrorMessage(error)).resolves.toBe("Kelas belum memiliki nilai final");
  });
});
