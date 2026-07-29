import axios from "axios";
import { appConfig } from "@/lib/config";
import { useAuthStore } from "@/stores/authStore";
import { logger } from "@/lib/logger";

export type LoginResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: string;
    email: string;
    full_name: string;
    role: string;
    status: string;
  };
};

const authClient = axios.create({
  baseURL: appConfig.apiBaseUrl,
  timeout: 30_000,
});

export async function loginRequest(email: string, password: string) {
  const { data } = await authClient.post<LoginResponse>("/auth/login", {
    email,
    password,
  });
  return data;
}

export async function refreshRequest(refreshToken: string) {
  const { data } = await authClient.post<LoginResponse>("/auth/refresh", {
    refresh_token: refreshToken,
  });
  return data;
}

export async function logoutRequest(refreshToken: string | null) {
  const access = useAuthStore.getState().accessToken;
  await authClient.post(
    "/auth/logout",
    { refresh_token: refreshToken },
    { headers: access ? { Authorization: `Bearer ${access}` } : {} },
  );
}

export async function fetchMe() {
  const access = useAuthStore.getState().accessToken;
  const { data } = await authClient.get("/auth/me", {
    headers: { Authorization: `Bearer ${access}` },
  });
  return data;
}

let refreshing: Promise<string | null> | null = null;

/** Attempt token refresh; returns new access token or null. */
export async function ensureFreshAccessToken(): Promise<string | null> {
  const { accessToken, refreshToken, setTokens, clearSession } =
    useAuthStore.getState();
  if (!refreshToken) return accessToken;

  if (!refreshing) {
    refreshing = (async () => {
      try {
        const data = await refreshRequest(refreshToken);
        setTokens(data.access_token, data.refresh_token);
        return data.access_token;
      } catch (err) {
        logger.warn("token_refresh_failed");
        clearSession();
        return null;
      } finally {
        refreshing = null;
      }
    })();
  }
  return refreshing;
}

export function friendlyApiError(status?: number, detail?: unknown): string {
  const msg =
    typeof detail === "object" && detail && "message" in detail
      ? String((detail as { message: string }).message)
      : typeof detail === "string"
        ? detail
        : undefined;

  switch (status) {
    case 401:
      return msg || "Session expired. Please sign in again.";
    case 403:
      return msg || "You do not have permission for this action.";
    case 404:
      return msg || "The requested resource was not found.";
    case 422:
      return msg || "Validation failed. Check your inputs.";
    case 500:
      return msg || "A server error occurred. Try again later.";
    default:
      return msg || "Network error. Check your connection and try again.";
  }
}
