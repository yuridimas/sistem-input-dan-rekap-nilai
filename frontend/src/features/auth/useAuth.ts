/**
 * Penghubung profil /auth/me, React Query, dan state sesi persisten.
 * Dipakai guard, layout, serta halaman yang memerlukan role/identitas pengguna.
 */
import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";

import api from "@/lib/api";
import { useAuthStore, type AuthUser } from "@/stores/authStore";

export const authQueryKey = ["auth", "me"] as const;

/**
 * Muat profil sesi aktif menggunakan client dengan mekanisme refresh bersama.
 * @returns Promise<AuthUser>; kegagalan HTTP diteruskan ke React Query.
 */
export async function fetchCurrentUser() {
  const { data } = await api.get<AuthUser>("/auth/me");
  return data;
}

/**
 * Tunggu hidrasi token sebelum memuat profil agar guard tidak mengalihkan terlalu awal.
 * @returns Profil/state loading/error dan refetch; efek menyelaraskan profil ke Zustand.
 */
export function useAuth() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const refreshToken = useAuthStore((state) => state.refreshToken);
  const hasHydrated = useAuthStore((state) => state.hasHydrated);
  const storedUser = useAuthStore((state) => state.user);
  const setUser = useAuthStore((state) => state.setUser);
  const hasTokens = Boolean(accessToken || refreshToken);

  const query = useQuery({
    queryKey: authQueryKey,
    queryFn: fetchCurrentUser,
    enabled: hasHydrated && hasTokens,
    retry: false,
  });

  useEffect(() => {
    if (query.data) setUser(query.data);
    if (!hasTokens && storedUser) setUser(null);
  }, [hasTokens, query.data, setUser, storedUser]);

  return {
    user: hasTokens ? query.data ?? storedUser : null,
    hasTokens,
    isLoading: !hasHydrated || (hasTokens && query.isPending),
    error: query.error,
    retry: query.refetch,
  };
}
