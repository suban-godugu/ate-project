import { setAccessToken } from "./config";
import { apiFetch } from "./client";

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  role: string;
  department?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const res = await apiFetch<TokenResponse>("/auth/login", {
    method: "POST",
    body: { email, password },
    auth: false,
  });
  setAccessToken(res.access_token);
  if (typeof window !== "undefined") {
    localStorage.setItem("verilumen_refresh_token", res.refresh_token);
  }
  return res;
}

export async function logout(): Promise<void> {
  try {
    await apiFetch("/auth/logout", { method: "POST" });
  } finally {
    setAccessToken(null);
    if (typeof window !== "undefined") {
      localStorage.removeItem("verilumen_refresh_token");
    }
  }
}

export async function getMe(): Promise<AuthUser> {
  return apiFetch("/auth/me");
}

export async function getPreferences(): Promise<{
  theme_json?: Record<string, unknown>;
  account_json?: Record<string, unknown>;
  filters_json?: Record<string, unknown>;
}> {
  return apiFetch("/users/me/preferences");
}

export async function updatePreferences(prefs: {
  theme_json?: Record<string, unknown>;
  account_json?: Record<string, unknown>;
  filters_json?: Record<string, unknown>;
}): Promise<void> {
  await apiFetch("/users/me/preferences", { method: "PATCH", body: prefs });
}

export const authApi = { login, logout, getMe, getPreferences, updatePreferences };
