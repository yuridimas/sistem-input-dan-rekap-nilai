/**
 * Guard route yang memakai useAuth untuk menunggu hidrasi dan validasi sesi.
 * Dipakai App pada seluruh halaman internal serta kelompok route superadmin.
 */
import { RefreshCw } from "lucide-react";
import { Navigate, Outlet, useLocation } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/useAuth";
import type { UserRole } from "@/stores/authStore";

/**
 * Simpan lokasi tujuan saat menuju login dan tampilkan retry ketika profil belum dapat
 * dimuat.
 * @param allowedRoles Filter role opsional; tanpa filter cukup memiliki profil sesi.
 * @returns Outlet, pengalihan, status/error sesi, atau null saat profil belum tersedia.
 */
export function ProtectedRoute({ allowedRoles }: { allowedRoles?: UserRole[] }) {
  const location = useLocation();
  const { user, hasTokens, isLoading, error, retry } = useAuth();

  if (isLoading) {
    return (
      <div className="grid min-h-screen place-items-center" role="status" aria-label="Memeriksa sesi">
        <div className="flex items-center gap-3 text-sm text-muted-foreground"><span className="size-4 animate-spin rounded-full border-2 border-current border-r-transparent" />Memeriksa sesi…</div>
      </div>
    );
  }

  if (!hasTokens) return <Navigate to="/login" replace state={{ from: location }} />;

  if (error && !user) {
    return (
      <main className="grid min-h-screen place-items-center px-5">
        <section className="max-w-sm text-center" aria-labelledby="session-error-title">
          <h1 className="text-xl font-semibold" id="session-error-title">Sesi belum dapat diperiksa</h1>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">Periksa koneksi ke server, lalu coba kembali.</p>
          <Button className="mt-5" onClick={() => void retry()} type="button"><RefreshCw className="size-4" aria-hidden="true" />Coba lagi</Button>
        </section>
      </main>
    );
  }

  if (!user) return null;
  if (allowedRoles && !allowedRoles.includes(user.role)) return <Navigate to="/dashboard" replace />;

  return <Outlet />;
}
