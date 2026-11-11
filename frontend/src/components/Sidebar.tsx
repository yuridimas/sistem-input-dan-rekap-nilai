/**
 * Navigasi bersama untuk Layout; item administratif mengikuti role profil sesi.
 * Batas tampilan menu melengkapi guard UI, sedangkan otorisasi tetap dilakukan backend.
 */
import { BookOpen, GraduationCap, LayoutDashboard, Users, X } from "lucide-react";
import { useRef, type KeyboardEvent } from "react";
import { Link, useLocation } from "react-router-dom";

import type { AuthUser } from "@/stores/authStore";
import { SessionProfile } from "@/components/SessionProfile";
import { getCourseMenuLabel, isSidebarItemActive } from "@/lib/navigation";

/**
 * Render navigasi desktop/mobile; onClose mengembalikan kendali fokus kepada Layout.
 */
export function Sidebar({ user, open, onClose, onLogout }: { user: AuthUser; open: boolean; onClose: () => void; onLogout: () => void }) {
  const sidebarRef = useRef<HTMLElement>(null);
  const { pathname } = useLocation();
  const items = [
    { label: "Dashboard", to: "/dashboard", icon: LayoutDashboard },
    { label: getCourseMenuLabel(user.role), to: "/courses", icon: BookOpen },
    { label: "Mahasiswa", to: "/students", icon: GraduationCap },
    ...(user.role === "superadmin" ? [{ label: "Pengguna", to: "/users", icon: Users }] : []),
  ];

  /**
   * Tahan siklus Tab di sidebar yang terbuka dan tutup lewat Escape.
   * Efek: fokus DOM; ketika sidebar tertutup, navigasi keyboard tidak dicegat.
   */
  function handleKeyDown(event: KeyboardEvent<HTMLElement>) {
    if (!open) return;
    if (event.key === "Escape") {
      onClose();
      return;
    }
    if (event.key !== "Tab") return;

    const focusable = sidebarRef.current?.querySelectorAll<HTMLElement>("a[href], button:not([disabled])");
    if (!focusable?.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  return (
    <>
      {open && <button aria-label="Tutup navigasi" className="fixed inset-0 z-30 bg-slate-950/40 lg:hidden" onClick={onClose} tabIndex={-1} type="button" />}
      <aside className={`fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r border-border bg-background px-4 py-5 transition-[transform,visibility] duration-200 lg:sticky lg:top-0 lg:h-screen lg:w-64 lg:visible lg:translate-x-0 ${open ? "visible translate-x-0" : "invisible -translate-x-full"}`} id="app-sidebar" onKeyDown={handleKeyDown} ref={sidebarRef}>
        <div className="flex items-center justify-between px-2">
          <div className="flex items-center gap-3">
            <span className="grid size-10 place-items-center rounded-xl bg-primary text-primary-foreground"><GraduationCap className="size-5" aria-hidden="true" /></span>
            <span><span className="block text-sm font-semibold">Sistem Nilai</span><span className="block text-xs text-muted-foreground">Ruang akademik</span></span>
          </div>
          <button aria-label="Tutup navigasi" className="grid size-9 place-items-center rounded-lg text-muted-foreground hover:bg-muted lg:hidden" id="close-sidebar" onClick={onClose} type="button"><X className="size-4" aria-hidden="true" /></button>
        </div>

        <div className="mt-10 px-3 text-xs font-medium uppercase tracking-wide text-muted-foreground">Menu utama</div>
        <nav aria-label="Navigasi utama" className="mt-3 flex flex-col gap-1">
          {items.map(({ label, to, icon: Icon }) => {
            const isActive = isSidebarItemActive(to, pathname);
            return <Link
              aria-current={isActive ? "page" : undefined}
              className={`flex min-h-10 items-center gap-3 rounded-lg px-3 text-sm font-medium outline-none transition focus-visible:ring-2 focus-visible:ring-ring ${isActive ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted hover:text-foreground"}`}
              key={to}
              onClick={onClose}
              to={to}
            >
              <Icon className="size-4" aria-hidden="true" />{label}
            </Link>;
          })}
        </nav>

        <SessionProfile onLogout={onLogout} user={user} />
      </aside>
    </>
  );
}
