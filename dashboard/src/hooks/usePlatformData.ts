"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  adjustHeatmapValues,
  adjustKPIValue,
  adjustSparkline,
  adjustTrendPoints,
  filterRowsByGlobal,
} from "@/lib/filterEngine";
import { executiveKPIs, patternAnalysisData, costTrendData } from "@/lib/dummyData";
import { getExecutive } from "@/lib/api/dashboard";
import { isLiveApi } from "@/lib/api/config";
import { hasLiveContent } from "@/hooks/liveDataUtils";
import { useFilterStore } from "@/stores/filterStore";
import type { ExecutiveKPI, PatternRow, CostTrendPoint } from "@/types/dashboard";

function buildExecutiveData(filters: ReturnType<typeof useFilterStore.getState>["filters"]) {
  const kpis: ExecutiveKPI[] = executiveKPIs.map((kpi, i) => ({
    ...kpi,
    value: adjustKPIValue(kpi.value, filters, i),
    sparkline: adjustSparkline(kpi.sparkline, filters),
  }));
  const patterns = filterRowsByGlobal(patternAnalysisData, filters);
  const costTrend: CostTrendPoint[] = costTrendData.map((point) => {
    const adjusted = adjustTrendPoints(
      [{ label: point.day, value: point.totalCost, value2: point.costPerWafer }],
      filters
    )[0]!;
    return {
      day: point.day,
      totalCost: adjusted.value,
      costPerWafer: adjusted.value2 ?? point.costPerWafer,
    };
  });
  return { kpis, patterns, costTrend };
}

const EMPTY_EXEC = { kpis: [] as ExecutiveKPI[], patterns: [] as PatternRow[], costTrend: [] as CostTrendPoint[] };

export function useFilteredExecutiveData() {
  const filters = useFilterStore((s) => s.filters);
  const live = isLiveApi();
  const mockData = useMemo(() => buildExecutiveData(filters), [filters]);

  const liveQuery = useQuery({
    queryKey: ["dashboard", "executive", filters],
    queryFn: () => getExecutive(filters),
    enabled: live,
    staleTime: 5 * 60_000,
    placeholderData: (previous) => previous,
  });

  const data = useMemo(() => {
    if (!live) return mockData;
    if (liveQuery.isLoading || liveQuery.isPending) return EMPTY_EXEC;
    if (liveQuery.isError || !liveQuery.data) return EMPTY_EXEC;
    const api = liveQuery.data;
    const costTrend =
      (api.charts?.costTrendLive as CostTrendPoint[] | undefined) ?? api.costTrend ?? [];
    return {
      kpis: api.kpis ?? [],
      patterns: api.patterns ?? [],
      costTrend,
    };
  }, [live, mockData, liveQuery.data, liveQuery.isLoading, liveQuery.isPending, liveQuery.isError]);

  const isEmpty =
    live &&
    !!liveQuery.data &&
    !liveQuery.isError &&
    !hasLiveContent({
      kpis: liveQuery.data.kpis ?? [],
      rows: (liveQuery.data.patterns ?? []) as unknown as Record<string, unknown>[],
      charts: liveQuery.data.charts,
    });

  return {
    data,
    isLoading: live ? liveQuery.isLoading || liveQuery.isPending : false,
    isFetching: live ? liveQuery.isFetching : false,
    isPending: live ? liveQuery.isPending : false,
    isError: live ? liveQuery.isError : false,
    isEmpty,
    error: live ? liveQuery.error : null,
    invalidate: () => liveQuery.refetch(),
    refetch: liveQuery.refetch,
  };
}

export function useFilteredModuleData<T extends object>(
  key: string,
  kpis: {
    id: string;
    title: string;
    value: string;
    change: number;
    trend: "up" | "down";
    sparkline: number[];
    icon: string;
    positiveIsGood?: boolean;
  }[],
  tableRows: T[]
) {
  const filters = useFilterStore((s) => s.filters);
  const live = isLiveApi();

  const data = useMemo(() => {
    if (live) {
      return { kpis: [], rows: [] as T[] };
    }
    return {
      kpis: kpis.map((kpi, i) => ({
        ...kpi,
        value: adjustKPIValue(kpi.value, filters, i),
        sparkline: adjustSparkline(kpi.sparkline, filters),
      })),
      rows: filterRowsByGlobal(tableRows, filters),
    };
  }, [live, filters, kpis, tableRows]);

  return {
    data,
    isLoading: false,
    isPending: false,
  };
}

export function useFilteredHeatmap(key: string, grid: number[][]) {
  const filters = useFilterStore((s) => s.filters);
  const live = isLiveApi();
  return useMemo(() => {
    if (live) return Array.from({ length: grid.length || 12 }, () => Array(grid[0]?.length || 12).fill(0));
    return adjustHeatmapValues(grid, filters);
  }, [key, grid, filters, live]);
}
