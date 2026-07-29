import type { DashboardTabData } from "@/lib/api/dashboard";

/** True when the API returned a successful payload with no KPIs, rows, or chart series. */
export function hasLiveContent(api: DashboardTabData): boolean {
  if (api.kpis?.length) return true;
  if (api.rows?.length) return true;
  const charts = api.charts;
  if (!charts) return false;
  return Object.values(charts).some((v) => {
    if (Array.isArray(v)) return v.length > 0;
    if (v && typeof v === "object") return Object.keys(v as object).length > 0;
    return v != null && v !== "";
  });
}

/** Strip mock arrays / chart generators for live mode — no silent mock fallback. */
export function emptyLiveShell<T extends Record<string, unknown>>(template: T): T {
  const out = { ...template } as Record<string, unknown>;
  for (const key of Object.keys(template)) {
    const val = template[key];
    if (Array.isArray(val)) {
      out[key] = [];
    } else if (typeof val === "function") {
      out[key] = () => [];
    }
  }
  return out as T;
}
