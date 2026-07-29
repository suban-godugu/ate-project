"use client";

import { useCallback } from "react";
import * as raw from "@/lib/mbistData";
import { getModuleTab } from "@/lib/api/dashboard";
import { useModuleDashboard } from "@/hooks/useModuleDashboard";
import { filterKPIArray, filterRows, wrapHeatmapGenerator } from "@/hooks/dataFilterUtils";
import type { GlobalFilters } from "@/types/platform";
import type { DashboardTabData } from "@/lib/api/dashboard";

const CHART_KEYS = [
  "memoryHealthData",
  "failureTypeDistribution",
  "failureTrend",
  "utilizationTrend",
  "failureByType",
  "failureByBankChart",
  "diagnosisTimeline",
  "failureCorrelation",
] as const;

function buildFilteredMbistData(filters: GlobalFilters) {
  return {
    overviewKPIs: filterKPIArray(raw.overviewKPIs, filters),
    memoryHealthKPIs: filterKPIArray(raw.memoryHealthKPIs, filters),
    failureKPIs: filterKPIArray(raw.failureKPIs, filters),
    diagnosisKPIs: filterKPIArray(raw.diagnosisKPIs, filters),
    memoryHealthData: raw.memoryHealthData,
    failureByBank: raw.failureByBank,
    recentFailures: filterRows(raw.recentFailures, filters),
    failureTypeDistribution: raw.failureTypeDistribution,
    aiDiagnosisSummary: raw.aiDiagnosisSummary,
    utilizationTrend: raw.utilizationTrend,
    temperatureTrend: raw.temperatureTrend,
    accessDistribution: raw.accessDistribution,
    memoryDensity: raw.memoryDensity,
    failureTrend: raw.failureTrend,
    failureByType: raw.failureByType,
    failureByBankChart: raw.failureByBankChart,
    failureRecords: filterRows(raw.failureRecords, filters),
    diagnosisTimeline: raw.diagnosisTimeline,
    failureCorrelation: raw.failureCorrelation,
    aiConfidenceTrend: raw.aiConfidenceTrend,
    diagnosisReports: filterRows(raw.diagnosisReports, filters),
    failAddressReport: filterRows(raw.failAddressReport, filters),
    repairRecommendations: filterRows(raw.repairRecommendations, filters),
    aiRecommendations: filterRows(raw.aiRecommendations, filters),
    riskCards: raw.riskCards,
    generateMemoryHeatmap: wrapHeatmapGenerator(raw.generateMemoryHeatmap, filters),
    connectivityNodes: raw.connectivityNodes,
  };
}

function applyMbistLive(
  base: ReturnType<typeof buildFilteredMbistData>,
  api: DashboardTabData,
  tab: string,
  filters: GlobalFilters
) {
  const kpis = (api.kpis ?? []) as typeof raw.overviewKPIs;
  const rows = filterRows((api.rows ?? []) as Record<string, unknown>[], filters);
  switch (tab) {
    case "memory-health":
      return { ...base, memoryHealthKPIs: kpis, recentFailures: rows as unknown as typeof raw.recentFailures };
    case "failure-analysis":
      return { ...base, failureKPIs: kpis, failureRecords: rows as unknown as typeof raw.failureRecords };
    case "diagnosis":
      return { ...base, diagnosisKPIs: kpis, diagnosisReports: rows as unknown as typeof raw.diagnosisReports };
    case "ai-recommendation":
      return { ...base, aiRecommendations: rows as unknown as typeof raw.aiRecommendations };
    default:
      return { ...base, overviewKPIs: kpis, recentFailures: rows as unknown as typeof raw.recentFailures };
  }
}

export function useFilteredMbistData() {
  const mockBuilder = useCallback((filters: GlobalFilters) => buildFilteredMbistData(filters), []);
  return useModuleDashboard("mbist", mockBuilder, [...CHART_KEYS], applyMbistLive, (tab, filters) =>
    getModuleTab("mbist", tab, filters)
  );
}

export type FilteredMbistData = ReturnType<typeof useFilteredMbistData>;
