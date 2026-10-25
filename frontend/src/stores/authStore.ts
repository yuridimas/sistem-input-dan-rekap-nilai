import { create } from "zustand";
import { persist } from "zustand/middleware";

export type UserRole = "superadmin" | "lecturer";

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

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
      partialize: ({ accessToken, refreshToken }) => ({ accessToken, refreshToken }),
      onRehydrateStorage: () => (state) => state?.setHasHydrated(true),
    }
  )
);
