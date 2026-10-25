import { useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { downloadReport, reportErrorMessage } from "./download";

export function ReportDownloadButton({
  path,
  filename,
  label,
  ariaLabel,
}: {
  path: string;
  filename: string;
  label: string;
  ariaLabel?: string;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleDownload() {
    setBusy(true);
    setError("");
    try {
      await downloadReport(path, filename);
    } catch (reason) {
      setError(await reportErrorMessage(reason));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col items-start gap-2">
      <Button aria-label={ariaLabel} disabled={busy} onClick={() => void handleDownload()} type="button" variant="outline">
        {busy ? "Menyiapkan unduhan…" : label}
      </Button>
      {error && <Alert className="max-w-sm" variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>}
    </div>
  );
}

export function ClassReportDownloads({ classId }: { classId: string }) {
  return (
    <div className="flex flex-wrap gap-2">
      <ReportDownloadButton
        filename="rekap-kelas.pdf"
        label="Unduh PDF"
        path={`/reports/class/${classId}/pdf`}
      />
      <ReportDownloadButton
        filename="rekap-kelas.xlsx"
        label="Unduh Excel"
        path={`/reports/class/${classId}/xlsx`}
      />
    </div>
  );
}
