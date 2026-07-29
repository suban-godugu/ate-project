export type ApiMode = "mock" | "live";

export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
}

export function getApiMode(): ApiMode {
  const mode = process.env.NEXT_PUBLIC_API_MODE;
  return mode === "live" ? "live" : "mock";
}

export function isLiveApi(): boolean {
  return getApiMode() === "live";
}

const ACCESS_TOKEN_KEY = "verilumen_access_token";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setAccessToken(token: string | null): void {
  if (typeof window === "undefined") return;
  if (token) localStorage.setItem(ACCESS_TOKEN_KEY, token);
  else localStorage.removeItem(ACCESS_TOKEN_KEY);
}
