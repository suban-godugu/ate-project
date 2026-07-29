import type {
  AnalyticsSummary,
  HealthResponse,
  OptimizationRecommendation,
  RecommendationListResponse,
  SamplesResponse,
} from "./types";

const BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: init?.body instanceof FormData ? undefined : { "Content-Type": "application/json" },
    ...init,
  });

  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = (await res.json()) as { detail?: string };
      if (body?.detail) detail = body.detail;
    } catch {
      // Response body was not JSON; keep the status-derived message.
    }
    throw new Error(detail);
  }

  return (await res.json()) as T;
}

export const api = {
  health: () => request<HealthResponse>("/health"),

  samples: () => request<SamplesResponse>("/samples"),

  optimizeSample: (name: string, persist = true) =>
    request<OptimizationRecommendation>(
      `/optimize/sample/${encodeURIComponent(name)}?persist=${persist}`,
      { method: "POST" },
    ),

  listRecommendations: (params: {
    q?: string;
    risk_level?: string;
    device?: string;
    limit?: number;
    offset?: number;
  } = {}) => {
    const search = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== "") search.set(key, String(value));
    });
    const qs = search.toString();
    return request<RecommendationListResponse>(`/recommendations${qs ? `?${qs}` : ""}`);
  },

  getRecommendation: (id: string) =>
    request<OptimizationRecommendation>(`/recommendations/${encodeURIComponent(id)}`),

  deleteRecommendation: (id: string) =>
    request<{ deleted: string }>(`/recommendations/${encodeURIComponent(id)}`, {
      method: "DELETE",
    }),

  compare: (ids: string[]) =>
    request<OptimizationRecommendation[]>("/recommendations/compare", {
      method: "POST",
      body: JSON.stringify({ ids }),
    }),

  analytics: () => request<AnalyticsSummary>("/analytics/summary"),

  upload: (file: File, persist = true) => {
    const form = new FormData();
    form.append("file", file);
    return request<OptimizationRecommendation>(`/upload?persist=${persist}`, {
      method: "POST",
      body: form,
    });
  },
};
