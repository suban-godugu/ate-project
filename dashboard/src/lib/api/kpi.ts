import { apiFetch, buildQuery } from "@/lib/api/client";
import type { KpiDrillDownFilters, KpiWorkspaceApiResponse } from "@/types/kpiDrillDown";

export function kpiFiltersToParams(filters: KpiDrillDownFilters): Record<string, string> {
  return {
    fab: filters.fab,
    tester: filters.tester,
    product: filters.product,
    lot: filters.lot,
    wafer: filters.wafer,
    date_preset: filters.timeRange,
  };
}

export async function getKpiWorkspace(
  kpiId: string,
  filters: KpiDrillDownFilters
): Promise<KpiWorkspaceApiResponse> {
  return apiFetch<KpiWorkspaceApiResponse>(
    `/kpi/${encodeURIComponent(kpiId)}/workspace${buildQuery(kpiFiltersToParams(filters))}`
  );
}
