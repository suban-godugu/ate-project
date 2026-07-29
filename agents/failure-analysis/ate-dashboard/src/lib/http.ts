/**
 * Shared Axios interceptors for JWT attachment, refresh, and friendly errors.
 */
import type { AxiosInstance, InternalAxiosRequestConfig } from "axios";
import { appConfig } from "@/lib/config";
import { logger } from "@/lib/logger";
import {
  ensureFreshAccessToken,
  friendlyApiError,
} from "@/services/auth";
import { useAuthStore } from "@/stores/authStore";
import { notify } from "@/stores/toastStore";

declare module "axios" {
  export interface AxiosRequestConfig {
    _retry?: boolean;
  }
}

export function configureApiClient(client: AxiosInstance) {
  client.defaults.baseURL = appConfig.apiBaseUrl;

  client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    // Preserve gateway-compatible identity headers for module RBAC
    const user = useAuthStore.getState().user;
    if (user) {
      config.headers["X-User-Id"] = user.id;
      config.headers["X-Role"] = user.role;
    }
    return config;
  });

  client.interceptors.response.use(
    (res) => res,
    async (error) => {
      const status = error.response?.status as number | undefined;
      const config = error.config;
      const detail = error.response?.data?.detail;
      const url = String(config?.url || "");

      logger.apiError(url, status || 0, friendlyApiError(status, detail));

      if (status === 401 && config && !config._retry && appConfig.authEnabled) {
        config._retry = true;
        const newToken = await ensureFreshAccessToken();
        if (newToken) {
          config.headers = config.headers || {};
          config.headers.Authorization = `Bearer ${newToken}`;
          return client.request(config);
        }
        if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
          window.location.href = `/login?next=${encodeURIComponent(window.location.pathname)}`;
        }
      }

      if (status === 403) {
        notify({
          title: "Access Denied",
          description: friendlyApiError(403, detail),
          variant: "error",
        });
      } else if (status && status >= 500) {
        notify({
          title: "Server Error",
          description: friendlyApiError(status, detail),
          variant: "error",
        });
      } else if (!error.response) {
        notify({
          title: "Network Error",
          description: "Request timed out or the backend is unreachable.",
          variant: "warning",
        });
      }

      return Promise.reject(error);
    },
  );
}
