import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

import { useAuthStore } from "@/stores/authStore";

const baseURL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

interface TokenPair {
  access_token: string;
  refresh_token: string;
}

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
