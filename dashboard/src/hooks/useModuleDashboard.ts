"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import type { DashboardTabData } from "@/lib/api/dashboard";
import { isLiveApi } from "@/lib/api/config";
import { useModuleTab } from "@/contexts/ModuleTabContext";
import { buildLiveModuleResult } from "@/hooks/useLiveModuleCharts";
import { useFilterStore } from "@/stores/filterStore";
import type { GlobalFilters } from "@/types/platform";

export function useModuleDashboard<T extends Record<string, unknown>>(
  module: string,
  mockBuilder: (filters: GlobalFilters) => T,
  chartKeys: (keyof T)[],
  applyLive: (base: T, api: DashboardTabData, tab: string, filters: GlobalFilters) => T,
  fetchTab: (tab: string, filters: GlobalFilters) => Promise<DashboardTabData>
) {
  const filters = useFilterStore((s) => s.filters);
  const tab = useModuleTab();
  const live = isLiveApi();

  const mockFiltered = useMemo(() => mockBuilder(filters), [mockBuilder, filters]);

  const query = useQuery({
    queryKey: ["dashboard", module, tab, filters],
    queryFn: () => fetchTab(tab, filters),
    enabled: live,
    staleTime: 5 * 60_000,
    placeholderData: (previous) => previous,
  });

  return buildLiveModuleResult(mockFiltered, query, live, chartKeys, (base, api) =>
    applyLive(base, api, tab, filters)
  );
}
