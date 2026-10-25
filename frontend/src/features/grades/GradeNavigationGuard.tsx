import { useBeforeUnload, useBlocker } from "react-router-dom";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { GradeEntry } from "./hooks";

export function GradeNavigationGuard({
  entry,
  classId,
}: {
  entry: GradeEntry;
  classId: string;
}) {
  const dirty =
    entry.engine.hasChanges() ||
    entry.snapshot.saving ||
    entry.finalizing ||
    entry.uncertain;
  const blocker = useBlocker(({ currentLocation, nextLocation }) =>
    Boolean(
      entry.hasTokens &&
      dirty &&
      nextLocation.pathname !== "/login" &&
      !(
        currentLocation.pathname === nextLocation.pathname &&
        nextLocation.pathname === `/classes/${classId}`
      ),
    ),
  );
  useBeforeUnload((event) => {
    if (entry.hasTokens && dirty) {
      event.preventDefault();
      event.returnValue = "";
    }
  });
  return (
    <Dialog
      open={blocker.state === "blocked"}
      onOpenChange={(open) => {
        if (!open && blocker.state === "blocked") blocker.reset();
      }}
    >
      <DialogContent
        showCloseButton={!entry.snapshot.saving && !entry.finalizing}
      >
        <DialogHeader>
          <DialogTitle>Perubahan nilai belum selesai</DialogTitle>
          <DialogDescription>
            {entry.snapshot.saving || entry.finalizing
              ? "Tunggu proses yang sedang berjalan sebelum meninggalkan kelas."
              : "Tetap di kelas untuk menyimpan atau buang perubahan lokal sebelum berpindah halaman."}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button
            onClick={() => {
              if (blocker.state === "blocked") blocker.reset();
            }}
            variant="outline"
          >
            Tetap di kelas
          </Button>
          <Button
            disabled={
              entry.snapshot.saving || entry.finalizing || entry.uncertain
            }
            onClick={() => {
              entry.engine.discard();
              if (blocker.state === "blocked") blocker.proceed();
            }}
            variant="destructive"
          >
            Buang perubahan
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
