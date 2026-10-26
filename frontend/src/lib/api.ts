/**
 * Client Axios bersama untuk seluruh API dengan bearer token dan refresh sesi.
 * Menggabungkan kegagalan 401 bersamaan agar rotasi refresh token hanya terjadi sekali.
 */
import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

import { useAuthStore } from "@/stores/authStore";

const baseURL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

/**
 * Hasil rotasi yang menggantikan kedua token pada auth store.
 */
interface TokenPair {
  access_token: string;
  refresh_token: string;
}

/**
 * Tanda retry internal mencegah request yang tetap 401 berulang tanpa batas.
 */
interface RetryableRequest extends InternalAxiosRequestConfig {
  _authRetry?: boolean;
}

let refreshRequest: Promise<TokenPair> | null = null;

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const request = error.config as RetryableRequest | undefined;
    const path = request?.url ?? "";
    // Cocokkan login/refresh hingga query atau akhir path agar refresh tidak rekursif.
    const isLoginOrRefresh = /\/auth\/(login|refresh)(?:\?|$)/.test(path);

    if (error.response?.status !== 401 || !request || request._authRetry || isLoginOrRefresh) {
      return Promise.reject(error);
    }

    const { refreshToken, setTokens, clear } = useAuthStore.getState();
    if (!refreshToken) {
      clear();
      return Promise.reject(error);
    }

    request._authRetry = true;
    try {
      // Semua 401 berbagi promise karena refresh token lama dicabut setelah rotasi.
      refreshRequest ??= axios
        .post<TokenPair>(`${baseURL}/auth/refresh`, { refresh_token: refreshToken })
        .then(({ data }) => data)
        .finally(() => {
          refreshRequest = null;
        });

      const tokens = await refreshRequest;
      setTokens(tokens.access_token, tokens.refresh_token);
      request.headers.Authorization = `Bearer ${tokens.access_token}`;
      return await api.request(request);
    } catch (refreshError) {
      clear();
      return Promise.reject(refreshError);
    }
  }
);

export default api;
