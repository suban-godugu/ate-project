import type { GlobalFilters } from "@/types/platform";
import type { ExecutiveKPI, PatternRow, CostTrendPoint } from "@/types/dashboard";
import type { SearchResultItem } from "@/types/platform";
import { apiFetch, buildQuery } from "./client";

function filtersToQuery(filters: GlobalFilters): Record<string, string | undefined> {
  return {
    date_preset: filters.datePreset,
    custom_date_from: filters.customDateFrom || undefined,
    custom_date_to: filters.customDateTo || undefined,
    fab: filters.fab || undefined,
    tester: filters.tester || undefined,
    product: filters.product || undefined,
    lot: filters.lot || undefined,
    wafer: filters.wafer || undefined,
  };
}

export interface DashboardTabData {
  kpis: ExecutiveKPI[];
  rows: Record<string, unknown>[];
  charts?: Record<string, unknown>;
}

export interface ExecutiveDashboardData {
  kpis: ExecutiveKPI[];
  patterns: PatternRow[];
  costTrend: CostTrendPoint[];
  charts?: Record<string, unknown>;
}

export interface IntegrationHealth {
  name: string;
  base_url: string;
  embed_path?: string | null;
  api_url?: string | null;
  reachable: boolean;
  dashboard_present: boolean;
  docs_present: boolean;
  latency_ms?: number | null;
  status_code?: number | null;
  error?: string | null;
}

export async function getExecutive(filters: GlobalFilters): Promise<ExecutiveDashboardData> {
  return apiFetch(`/dashboard/executive${buildQuery(filtersToQuery(filters))}`);
}

export async function getModuleTab(
  module: string,
  tab: string,
  filters: GlobalFilters
): Promise<DashboardTabData> {
  return apiFetch(`/dashboard/${module}/${tab}${buildQuery(filtersToQuery(filters))}`);
}

export async function getWaferOverview(filters: GlobalFilters): Promise<DashboardTabData> {
  return apiFetch(`/dashboard/wafer-analysis/overview${buildQuery(filtersToQuery(filters))}`);
}

export async function getWaferDefectClass(
  defectClass: string,
  filters: GlobalFilters
): Promise<DashboardTabData> {
  return apiFetch(`/dashboard/wafer-analysis/${defectClass}${buildQuery(filtersToQuery(filters))}`);
}

export async function getRecommendationAgent(
  agent: string,
  filters: GlobalFilters
): Promise<DashboardTabData> {
  return apiFetch(`/dashboard/recommendation-analysis/${agent}${buildQuery(filtersToQuery(filters))}`);
}

export async function getCostIntelligence(
  tab: string,
  filters: GlobalFilters
): Promise<DashboardTabData> {
  return apiFetch(`/dashboard/cost-intelligence/${tab}${buildQuery(filtersToQuery(filters))}`);
}

export async function getAlertsTab(tab: string, filters: GlobalFilters): Promise<DashboardTabData> {
  return apiFetch(`/dashboard/alerts/${tab}${buildQuery(filtersToQuery(filters))}`);
}

export async function searchPlatform(q: string): Promise<SearchResultItem[]> {
  return apiFetch(`/search${buildQuery({ q })}`, { auth: false });
}

export async function getFilterOptions() {
  return apiFetch<typeof import("@/types/platform").FILTER_OPTIONS>("/filters/options", { auth: false });
}

export async function getPatternAgentHealth(): Promise<IntegrationHealth> {
  return apiFetch("/integrations/pattern-agent/health", { auth: false });
}

export async function getFailureAgentHealth(): Promise<IntegrationHealth> {
  return apiFetch("/integrations/failure-agent/health", { auth: false });
}

export async function getScanDiagnosisAgentHealth(): Promise<IntegrationHealth> {
  return apiFetch("/integrations/scan-diagnosis-agent/health", { auth: false });
}

export async function getPatternRecommendationAgentHealth(): Promise<IntegrationHealth> {
  return apiFetch("/integrations/pattern-recommendation-agent/health", { auth: false });
}

export async function getScanDebugRecommendationAgentHealth(): Promise<IntegrationHealth> {
  return apiFetch("/integrations/scan-debug-recommendation-agent/health", { auth: false });
}

export async function getTestOptimizationAgentHealth(): Promise<IntegrationHealth> {
  return apiFetch("/integrations/test-optimization-agent/health", { auth: false });
}

export const dashboardApi = {
  getExecutive,
  getModuleTab,
  getWaferOverview,
  getWaferDefectClass,
  getRecommendationAgent,
  getCostIntelligence,
  getAlertsTab,
  searchPlatform,
  getFilterOptions,
  getPatternAgentHealth,
  getFailureAgentHealth,
  getScanDiagnosisAgentHealth,
  getPatternRecommendationAgentHealth,
  getScanDebugRecommendationAgentHealth,
  getTestOptimizationAgentHealth,
};
