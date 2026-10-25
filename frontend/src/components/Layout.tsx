import { LogOut, Menu } from "lucide-react";
import { useRef, useState } from "react";
import { flushSync } from "react-dom";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Sidebar } from "@/components/Sidebar";
import { useAuth } from "@/features/auth/useAuth";
import { useAuthStore } from "@/stores/authStore";

const pageTitles: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/courses": "Mata Kuliah",
  "/users": "Pengguna",
};

export function Layout() {
  const [menuOpen, setMenuOpen] = useState(false);
  const { user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const clear = useAuthStore((state) => state.clear);
  const menuButtonRef = useRef<HTMLButtonElement>(null);

  if (!user) return null;

  function logout() {
    clear();
    queryClient.removeQueries({ queryKey: ["auth"] });
    navigate("/login", { replace: true });
  }

  function closeMenu() {
    setMenuOpen(false);
    menuButtonRef.current?.focus();
  }

  function openMenu() {
    flushSync(() => setMenuOpen(true));
    window.setTimeout(() => document.getElementById("close-sidebar")?.focus(), 50);
  }

  const initials = user.full_name.split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase();

  return (
    <div className="min-h-screen bg-muted/30 lg:flex">
      <Sidebar user={user} open={menuOpen} onClose={closeMenu} />
      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-border bg-background/95 px-4 backdrop-blur sm:px-7">
          <div className="flex items-center gap-3">
            <button aria-label="Buka navigasi" aria-controls="app-sidebar" aria-expanded={menuOpen} className="grid size-9 place-items-center rounded-lg border border-border lg:hidden" onClick={openMenu} ref={menuButtonRef} type="button"><Menu className="size-4" aria-hidden="true" /></button>
            <div><p className="text-sm font-semibold">{pageTitles[location.pathname] ?? "Ruang kerja"}</p><p className="hidden text-xs text-muted-foreground sm:block">Sistem Input &amp; Rekap Nilai</p></div>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden text-right sm:block"><p className="max-w-48 truncate text-sm font-medium">{user.full_name}</p><p className="text-xs text-muted-foreground">{user.email}</p></div>
            <span aria-hidden="true" className="grid size-9 place-items-center rounded-full bg-secondary text-xs font-semibold text-secondary-foreground">{initials}</span>
            <Button aria-label="Keluar" className="size-9" onClick={logout} title="Keluar" type="button" variant="ghost"><LogOut className="size-4" aria-hidden="true" /><span className="sr-only">Keluar</span></Button>
          </div>
        </header>
        <main className="p-4 sm:p-7 lg:p-9"><Outlet /></main>
      </div>
    </div>
  );
}
