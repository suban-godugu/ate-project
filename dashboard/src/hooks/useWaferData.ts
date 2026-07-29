"use client";

import { useCallback } from "react";
import * as raw from "@/lib/waferData";
import { getWaferDefectClass, getWaferOverview } from "@/lib/api/dashboard";
import { gridFromApi } from "@/lib/api/mergeLiveDashboard";
import { useModuleDashboard } from "@/hooks/useModuleDashboard";
import {
  filterHeatmapGrid,
  filterKPIArray,
  filterRows,
  filterSparklineArray,
} from "@/hooks/dataFilterUtils";
import type { GlobalFilters } from "@/types/platform";
import type { DashboardTabData } from "@/lib/api/dashboard";

const CHART_KEYS = [
  "defectClassBreakdown",
  "defectTrend",
  "yieldTrend30",
  "yieldTrend",
  "positiveNegativeYield",
] as const;

function buildFilteredWaferData(filters: GlobalFilters) {
  return {
    buildWaferImages: raw.buildWaferImages,
    ANALYSIS_GRID: raw.ANALYSIS_GRID,
    getDieFailIntensity: raw.getDieFailIntensity,
    isDieFail: raw.isDieFail,
    WAFER_DEFECT_CLASSES: raw.WAFER_DEFECT_CLASSES,
    defectClassMeta: raw.defectClassMeta,
    inputDieStatsKPIs: filterKPIArray(raw.inputDieStatsKPIs, filters),
    defectClassificationKPIs: filterSparklineArray(raw.defectClassificationKPIs, filters),
    positiveNegativeYield: raw.positiveNegativeYield,
    yieldTrend30: raw.yieldTrend30,
    yieldDistribution: raw.yieldDistribution,
    defectClassBreakdown: raw.defectClassBreakdown,
    topDefectWafers: filterRows(raw.topDefectWafers, filters),
    galleryCards: filterRows(raw.galleryCards, filters),
    bottomSummary: raw.bottomSummary,
    uploadWorkflowSteps: raw.uploadWorkflowSteps,
    defectClassBundles: raw.defectClassBundles,
    getDefectBundle: raw.getDefectBundle,
    overviewKPIs: filterKPIArray(raw.overviewKPIs, filters),
    yieldRows: filterRows(raw.yieldRows, filters),
    defectRows: filterRows(raw.defectRows, filters),
    yieldTrend: raw.yieldTrend,
    defectTrend: raw.defectTrend,
    waferRecommendations: filterRows(raw.waferRecommendations, filters),
    waferHeatmapGrid: filterHeatmapGrid(raw.waferHeatmapGrid, filters),
  };
}

function fetchWaferTab(tab: string, filters: GlobalFilters) {
  return tab === "overview" ? getWaferOverview(filters) : getWaferDefectClass(tab, filters);
}

function applyWaferLive(
  base: ReturnType<typeof buildFilteredWaferData>,
  api: DashboardTabData,
  tab: string,
  filters: GlobalFilters
) {
  const kpis = (api.kpis ?? []) as typeof raw.overviewKPIs;
  const rows = filterRows((api.rows ?? []) as Record<string, unknown>[], filters);
  const grid = api.charts?.waferHeatmapGrid as number[][] | undefined;
  if (tab === "overview") {
    return {
      ...base,
      overviewKPIs: kpis,
      topDefectWafers: rows as unknown as typeof raw.topDefectWafers,
      waferHeatmapGrid: grid ? gridFromApi(grid, 12, 12) : base.waferHeatmapGrid,
    };
  }
  return {
    ...base,
    defectClassificationKPIs: kpis as unknown as typeof raw.defectClassificationKPIs,
    defectRows: rows as unknown as typeof raw.defectRows,
  };
}

export function useFilteredWaferData() {
  const mockBuilder = useCallback((filters: GlobalFilters) => buildFilteredWaferData(filters), []);
  return useModuleDashboard("wafer-analysis", mockBuilder, [...CHART_KEYS], applyWaferLive, fetchWaferTab);
}

export type FilteredWaferData = ReturnType<typeof useFilteredWaferData>;
