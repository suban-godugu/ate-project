"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import type { DrillDownKPI } from "@/types/kpiDrillDown";
import type { KpiDrillDownFilters, KpiWorkspaceData } from "@/types/kpiDrillDown";
import {
  buildKpiWorkspace,
  defaultDrillDownFilters,
} from "@/lib/kpiDrillDown/buildKpiWorkspace";
import { getKpiWorkspace } from "@/lib/api/kpi";
import { isLiveApi } from "@/lib/api/config";
import { useFilterStore } from "@/stores/filterStore";

function mergeWorkspace(kpi: DrillDownKPI, apiWorkspace: Omit<KpiWorkspaceData, "kpi">): KpiWorkspaceData {
  return {
    kpi,
    ...apiWorkspace,
    header: {
      ...apiWorkspace.header,
      name: apiWorkspace.header.name || kpi.title,
      currentValue: apiWorkspace.header.currentValue || kpi.value,
      icon: apiWorkspace.header.icon || kpi.icon,
    },
  };
}

/**
 * KPI drill-down workspace — mock builder in dev, FastAPI in live mode.
 * Live: GET /api/v1/kpi/{kpiId}/workspace
 */
export function useKpiDrillDownWorkspace(kpi: DrillDownKPI | null) {
  const queryClient = useQueryClient();
  const globalFilters = useFilterStore((s) => s.filters);
  const [localFilters, setLocalFilters] = useState<KpiDrillDownFilters>(() =>
    defaultDrillDownFilters({
      fab: globalFilters.fab,
      tester: globalFilters.tester,
      product: globalFilters.product,
      lot: globalFilters.lot,
      wafer: globalFilters.wafer,
    })
  );
  const [mockRefreshKey, setMockRefreshKey] = useState(0);

  const live = isLiveApi();
  const enabled = Boolean(kpi) && live;

  const query = useQuery({
    queryKey: ["kpi-workspace", kpi?.id, localFilters, live],
    enabled,
    queryFn: async () => {
      if (!kpi) throw new Error("KPI required");
      const response = await getKpiWorkspace(kpi.id, localFilters);
      return mergeWorkspace(kpi, response.workspace);
    },
    staleTime: 60_000,
    retry: 1,
  });

  const mockWorkspace = useMemo(() => {
    if (!kpi || live) return null;
    void mockRefreshKey;
    return buildKpiWorkspace(kpi, localFilters);
  }, [kpi, localFilters, live, mockRefreshKey]);

  const workspace = live ? query.data ?? null : mockWorkspace;
  const isLoading = live ? query.isLoading || query.isFetching : false;
  const error = live && query.isError ? (query.error instanceof Error ? query.error.message : "Failed to load KPI workspace.") : null;

  const updateFilters = useCallback((partial: Partial<KpiDrillDownFilters>) => {
    setLocalFilters((prev) => ({ ...prev, ...partial }));
  }, []);

  const refresh = useCallback(() => {
    if (live && kpi) {
      void queryClient.invalidateQueries({ queryKey: ["kpi-workspace", kpi.id] });
    } else {
      setMockRefreshKey((k) => k + 1);
    }
  }, [live, kpi, queryClient]);

  useEffect(() => {
    setLocalFilters(
      defaultDrillDownFilters({
        fab: globalFilters.fab,
        tester: globalFilters.tester,
        product: globalFilters.product,
        lot: globalFilters.lot,
        wafer: globalFilters.wafer,
      })
    );
  }, [globalFilters.fab, globalFilters.tester, globalFilters.product, globalFilters.lot, globalFilters.wafer]);

  const isEmpty = !isLoading && !error && kpi !== null && workspace === null;

  return {
    workspace,
    filters: localFilters,
    updateFilters,
    refresh,
    isLoading,
    error,
    isEmpty,
    isLive: live,
  };
}
