import { getAccessToken, getApiBaseUrl } from "./config";
import { refreshAccessToken } from "./authRefresh";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type RequestOptions = Omit<RequestInit, "body"> & { body?: unknown; auth?: boolean };

async function doFetch(path: string, options: RequestOptions, token: string | null) {
  const { body, auth = true, headers: customHeaders, ...rest } = options;
  const headers: Record<string, string> = {
    ...(customHeaders as Record<string, string>),
  };
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (auth && token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return fetch(`${getApiBaseUrl()}${path}`, {
    ...rest,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
}

async function forceReLogin(): Promise<void> {
  if (typeof window === "undefined") return;
  const { clearSessionTokens } = await import("./authRefresh");
  clearSessionTokens();
  try {
    const { useUserStore } = await import("@/stores/userStore");
    useUserStore.getState().clearSession();
  } catch {
    /* store may be unavailable outside React */
  }
  if (!window.location.pathname.startsWith("/login")) {
    window.location.assign("/login");
  }
}

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { auth = true } = options;
  let token = auth ? getAccessToken() : null;

  // Access token often expires (or is cleared) while Zustand still looks "logged in".
  if (auth && !token) {
    token = await refreshAccessToken();
    if (!token) {
      await forceReLogin();
      throw new ApiError("API 401: Unauthorized", 401);
    }
  }

  let res = await doFetch(path, options, token);

  if (res.status === 401 && auth) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      token = newToken;
      res = await doFetch(path, options, token);
    }
  }

  if (!res.ok) {
    if (res.status === 401 && auth) {
      await forceReLogin();
    }
    let detail: unknown;
    try {
      detail = await res.json();
    } catch {
      detail = await res.text();
    }
    throw new ApiError(`API ${res.status}: ${res.statusText}`, res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  const contentType = res.headers.get("content-type");
  if (contentType?.includes("application/json")) {
    return res.json() as Promise<T>;
  }
  return res.text() as Promise<T>;
}

export function buildQuery(params: Record<string, string | undefined>): string {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== "") qs.set(k, v);
  }
  const s = qs.toString();
  return s ? `?${s}` : "";
}

export async function subscribeJobEvents(
  jobId: string,
  onEvent: (data: Record<string, unknown>) => void,
  pathPrefix = "/actions"
): Promise<() => void> {
  let token = getAccessToken();
  const url = `${getApiBaseUrl()}${pathPrefix}/${jobId}/status`;
  const controller = new AbortController();

  async function connect(authToken: string | null) {
    return fetch(url, {
      headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
      signal: controller.signal,
    });
  }

  let res = await connect(token);
  if (res.status === 401) {
    token = await refreshAccessToken();
    res = await connect(token);
  }
  if (!res.ok || !res.body) throw new ApiError("SSE connection failed", res.status);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  (async () => {
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";
        for (const part of parts) {
          const line = part.replace(/^data: /, "").trim();
          if (line) onEvent(JSON.parse(line));
        }
      }
    } catch {
      /* aborted */
    }
  })();

  return () => controller.abort();
}
