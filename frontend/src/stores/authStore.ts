/**
 * State sesi Zustand untuk client HTTP, useAuth, dan guard router.
 * Hanya token dipersistenkan; profil diperbarui dari server setelah hidrasi.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";

/**
 * Role yang dikenali navigasi; otorisasi sebenarnya tetap diperiksa backend.
 */
export type UserRole = "superadmin" | "lecturer";

/**
 * Profil /auth/me tanpa data password; dipakai penamaan UI dan pembatasan tampilan.
 */
export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

/**
 * Pisahkan token, profil, dan hidrasi agar startup tidak menganggap storage sudah siap.
 */
interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: AuthUser | null;
  hasHydrated: boolean;
  setTokens: (accessToken: string, refreshToken?: string | null) => void;
  setUser: (user: AuthUser | null) => void;
  setHasHydrated: (hasHydrated: boolean) => void;
  clear: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      hasHydrated: false,
      setTokens: (accessToken, refreshToken = null) =>
        set({ accessToken, refreshToken, user: null }),
      setUser: (user) => set({ user }),
      setHasHydrated: (hasHydrated) => set({ hasHydrated }),
      clear: () => set({ accessToken: null, refreshToken: null, user: null }),
    }),
    {
      name: "auth-store",
      // Profil tidak dipersistenkan agar role lama tidak dipercaya sebagai identitas sesi baru.
      partialize: ({ accessToken, refreshToken }) => ({ accessToken, refreshToken }),
      onRehydrateStorage: () => (state) => state?.setHasHydrated(true),
    }
  )
);
