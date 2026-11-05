/** Profil sesi dan aksi keluar yang selalu berada di bagian bawah sidebar. */
import { LogOut } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { AuthUser } from "@/stores/authStore";

/** Tampilkan satu salinan identitas sesi dan serahkan efek logout ke Layout. */
export function SessionProfile({ user, onLogout }: { user: AuthUser; onLogout: () => void }) {
  const initials = user.full_name.split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase();

  return (
    <div className="mt-auto rounded-xl border border-border bg-muted/40 p-3">
      <div className="flex min-w-0 items-center gap-3">
        <span aria-hidden="true" className="grid size-10 shrink-0 place-items-center rounded-full bg-secondary text-xs font-semibold text-secondary-foreground">{initials}</span>
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold">{user.full_name}</p>
          <p className="truncate text-xs text-muted-foreground">{user.email}</p>
          <p className="mt-0.5 text-xs text-muted-foreground">{user.role === "superadmin" ? "Superadmin" : "Dosen"}</p>
        </div>
      </div>
      <Button aria-label="Keluar" className="mt-3 w-full justify-start" onClick={onLogout} type="button" variant="outline">
        <LogOut aria-hidden="true" />
        Keluar
      </Button>
    </div>
  );
}
