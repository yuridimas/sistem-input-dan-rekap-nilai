/**
 * Shell halaman terlindungi yang dipasang router App.
 * Menampung sidebar responsif, profil sesi, dan Suspense untuk halaman lazy.
 */
import { Bell, Menu } from "lucide-react";
import { Suspense, useRef, useState } from "react";
import { flushSync } from "react-dom";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";

import { Sidebar } from "@/components/Sidebar";
import { useAuth } from "@/features/auth/useAuth";
import { useAuthStore } from "@/stores/authStore";

const pageTitles: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/courses": "Mata Kuliah",
  "/users": "Pengguna",
  "/notifications": "Status notifikasi",
  "/students": "Mahasiswa",
};

/**
 * Sajikan shell hanya ketika profil tersedia; Outlet memasang halaman yang sedang aktif.
 */
export function Layout() {
  const [menuOpen, setMenuOpen] = useState(false);
  const { user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const clear = useAuthStore((state) => state.clear);
  const menuButtonRef = useRef<HTMLButtonElement>(null);

  if (!user) return null;

  /**
   * Hapus token/profil sesi dan cache auth lalu ganti route ke login.
   * Efek: Zustand/storage, React Query, dan history browser; tidak memanggil endpoint
   * logout.
   */
  function logout() {
    clear();
    queryClient.removeQueries({ queryKey: ["auth"] });
    navigate("/login", { replace: true });
  }

  /**
   * Tutup sidebar mobile dan kembalikan fokus ke tombol pembuka.
   */
  function closeMenu() {
    setMenuOpen(false);
    menuButtonRef.current?.focus();
  }

  /**
   * Mount sidebar secara sinkron sebelum menunda fokus hingga elemen tombol tersedia.
   */
  function openMenu() {
    flushSync(() => setMenuOpen(true));
    window.setTimeout(() => document.getElementById("close-sidebar")?.focus(), 50);
  }

  return (
    <div className="min-h-screen bg-muted/30 lg:flex">
      <Sidebar onLogout={logout} user={user} open={menuOpen} onClose={closeMenu} />
      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-border bg-background/95 px-4 backdrop-blur sm:px-7">
          <div className="flex items-center gap-3">
            <button aria-label="Buka navigasi" aria-controls="app-sidebar" aria-expanded={menuOpen} className="grid size-9 place-items-center rounded-lg border border-border lg:hidden" onClick={openMenu} ref={menuButtonRef} type="button"><Menu className="size-4" aria-hidden="true" /></button>
            <div><p className="text-sm font-semibold">{pageTitles[location.pathname] ?? (location.pathname.startsWith("/courses/") ? "Detail Mata Kuliah" : location.pathname.startsWith("/classes/") ? "Detail Kelas" : "Ruang kerja")}</p><p className="hidden text-xs text-muted-foreground sm:block">Sistem Input &amp; Rekap Nilai</p></div>
          </div>
          <div className="flex items-center gap-3">
            {user.role === "superadmin" && (
              <Link aria-label="Buka notifikasi" className="grid size-9 place-items-center rounded-lg border border-border text-muted-foreground hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" to="/notifications">
                <Bell aria-hidden="true" className="size-4" />
                <span className="sr-only">Notifikasi</span>
              </Link>
            )}
          </div>
        </header>
        <main className="p-4 sm:p-7 lg:p-9"><Suspense fallback={<p className="text-sm text-muted-foreground" role="status">Memuat halaman…</p>}><Outlet /></Suspense></main>
      </div>
    </div>
  );
}
