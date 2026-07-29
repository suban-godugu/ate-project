import type { UseQueryResult } from "@tanstack/react-query";
import type { DashboardTabData } from "@/lib/api/dashboard";
import { mergeLiveCharts } from "@/lib/api/mergeLiveDashboard";
import { emptyLiveShell, hasLiveContent } from "@/hooks/liveDataUtils";

export function buildLiveModuleResult<T extends Record<string, unknown>>(
  mockFiltered: T,
  query: UseQueryResult<DashboardTabData>,
  live: boolean,
  chartKeys: (keyof T)[],
  applyRows: (base: T, api: DashboardTabData) => T
) {
  const status = {
    isLoading: live && (query.isLoading || query.isPending),
    isFetching: live && query.isFetching,
    isError: live && query.isError,
    isEmpty: false as boolean,
    error: live ? query.error : null,
    refetch: query.refetch,
  };

  if (!live) {
    return { ...mockFiltered, ...status, isLoading: false, isFetching: false, isError: false, isEmpty: false, error: null };
  }

  const shell = emptyLiveShell(mockFiltered);

  if (status.isLoading) {
    return { ...shell, ...status };
  }

  if (status.isError) {
    return { ...shell, ...status, isLoading: false, isFetching: false };
  }

  if (!query.data) {
    return { ...shell, ...status, isLoading: false, isFetching: query.isFetching, isEmpty: true };
  }

  const withCharts = mergeLiveCharts(shell, query.data, chartKeys, true);
  const merged = applyRows(withCharts, query.data);
  const isEmpty = !hasLiveContent(query.data);
  const chartMeta =
    live && query.data?.charts && typeof query.data.charts._meta === "object"
      ? (query.data.charts._meta as Record<string, unknown>)
      : undefined;

  return {
    ...merged,
    ...status,
    isLoading: false,
    isEmpty,
    isError: false,
    error: null,
    chartMeta,
    liveCharts: live ? query.data?.charts : undefined,
  };
}
