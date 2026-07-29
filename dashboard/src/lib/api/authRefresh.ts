import { getAccessToken, getApiBaseUrl, setAccessToken } from "./config";
import { ApiError } from "./client";

const REFRESH_TOKEN_KEY = "verilumen_refresh_token";

export async function refreshAccessToken(): Promise<string | null> {
  if (typeof window === "undefined") return null;
  const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
  if (!refreshToken) return null;

  try {
    const res = await fetch(`${getApiBaseUrl()}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) return null;

    const data = (await res.json()) as { access_token: string; refresh_token: string };
    setAccessToken(data.access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token);
    return data.access_token;
  } catch {
    // Backend unreachable (Failed to fetch) — treat as logged out, don't crash UI.
    return null;
  }
}

export function clearSessionTokens() {
  setAccessToken(null);
  if (typeof window !== "undefined") {
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }
}

