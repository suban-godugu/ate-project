"use client";

import { useCallback } from "react";
import * as raw from "@/lib/alertsData";
import { getAlertsTab } from "@/lib/api/dashboard";
import { useModuleDashboard } from "@/hooks/useModuleDashboard";
import { filterKPIArray, filterRows, wrapHeatmapGenerator } from "@/hooks/dataFilterUtils";
import type { GlobalFilters } from "@/types/platform";
import type { DashboardTabData } from "@/lib/api/dashboard";

const CHART_KEYS = ["alertDistribution", "severityDistribution", "alertTrend", "moduleAlertTrend"] as const;

function buildFilteredAlertsData(filters: GlobalFilters) {
  return {
    overviewKPIs: filterKPIArray(raw.overviewKPIs, filters),
    scanChainKPIs: filterKPIArray(raw.scanChainKPIs, filters),
    mbistKPIs: filterKPIArray(raw.mbistKPIs, filters),
    lbistKPIs: filterKPIArray(raw.lbistKPIs, filters),
    waferKPIs: filterKPIArray(raw.waferKPIs, filters),
    costKPIs: filterKPIArray(raw.costKPIs, filters),
    aiRecKPIs: filterKPIArray(raw.aiRecKPIs, filters),
    alertDistribution: raw.alertDistribution,
    severityDistribution: raw.severityDistribution,
    alertTrend: raw.alertTrend,
    recentAlerts: filterRows(raw.recentAlerts, filters),
    criticalAlertSummary: raw.criticalAlertSummary,
    executiveAlertSummary: raw.executiveAlertSummary,
    scanChainAlerts: filterRows(raw.scanChainAlerts, filters),
    mbistAlerts: filterRows(raw.mbistAlerts, filters),
    lbistAlerts: filterRows(raw.lbistAlerts, filters),
    waferAlerts: filterRows(raw.waferAlerts, filters),
    costAlerts: filterRows(raw.costAlerts, filters),
    aiRecommendationAlerts: filterRows(raw.aiRecommendationAlerts, filters),
    moduleAlertTrend: raw.moduleAlertTrend,
    generateWaferAlertHeatmap: wrapHeatmapGenerator(raw.generateWaferAlertHeatmap, filters),
  };
}

function applyAlertsLive(
  base: ReturnType<typeof buildFilteredAlertsData>,
  api: DashboardTabData,
  tab: string,
  filters: GlobalFilters
) {
  const kpis = (api.kpis ?? []) as typeof raw.overviewKPIs;
  const rows = filterRows((api.rows ?? []) as Record<string, unknown>[], filters);
  const tabMap: Record<string, keyof ReturnType<typeof buildFilteredAlertsData>> = {
    "scan-chain": "scanChainAlerts",
    mbist: "mbistAlerts",
    lbist: "lbistAlerts",
    wafer: "waferAlerts",
    cost: "costAlerts",
    "ai-recommendation": "aiRecommendationAlerts",
  };
  const kpiMap: Record<string, keyof ReturnType<typeof buildFilteredAlertsData>> = {
    "scan-chain": "scanChainKPIs",
    mbist: "mbistKPIs",
    lbist: "lbistKPIs",
    wafer: "waferKPIs",
    cost: "costKPIs",
    "ai-recommendation": "aiRecKPIs",
  };
  if (tab === "overview") {
    return { ...base, overviewKPIs: kpis, recentAlerts: rows as unknown as typeof raw.recentAlerts };
  }
  const rowKey = tabMap[tab];
  const kpiKey = kpiMap[tab];
  if (rowKey && kpiKey) {
    return { ...base, [kpiKey]: kpis, [rowKey]: rows };
  }
  return base;
}

export function useFilteredAlertsData() {
  const mockBuilder = useCallback((filters: GlobalFilters) => buildFilteredAlertsData(filters), []);
  return useModuleDashboard("alerts", mockBuilder, [...CHART_KEYS], applyAlertsLive, getAlertsTab);
}

export type FilteredAlertsData = ReturnType<typeof useFilteredAlertsData>;
