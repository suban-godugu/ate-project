"use client";

import { useCallback } from "react";
import * as raw from "@/lib/lbistData";
import { getModuleTab } from "@/lib/api/dashboard";
import { useModuleDashboard } from "@/hooks/useModuleDashboard";
import { filterKPIArray, filterRows, wrapHeatmapGenerator } from "@/hooks/dataFilterUtils";
import type { GlobalFilters } from "@/types/platform";
import type { DashboardTabData } from "@/lib/api/dashboard";

const CHART_KEYS = [
  "coverageDistribution",
  "failureTypeDistribution",
  "failureTrend",
  "coverageTrend",
  "coverageByBlock",
  "failureByModule",
  "patternEfficiency",
] as const;

function buildFilteredLbistData(filters: GlobalFilters) {
  return {
    overviewKPIs: filterKPIArray(raw.overviewKPIs, filters),
    coverageKPIs: filterKPIArray(raw.coverageKPIs, filters),
    failureKPIs: filterKPIArray(raw.failureKPIs, filters),
    diagnosisKPIs: filterKPIArray(raw.diagnosisKPIs, filters),
    coverageDistribution: raw.coverageDistribution,
    failureByModule: raw.failureByModule,
    recentFailures: filterRows(raw.recentFailures, filters),
    failureTypeDistribution: raw.failureTypeDistribution,
    aiDiagnosisSummary: raw.aiDiagnosisSummary,
    coverageTrend: raw.coverageTrend,
    coverageByBlock: raw.coverageByBlock,
    patternEfficiency: raw.patternEfficiency,
    faultDetectionRate: raw.faultDetectionRate,
    failureTrend: raw.failureTrend,
    failureByBlock: raw.failureByBlock,
    failureDensity: raw.failureDensity,
    failureRecords: filterRows(raw.failureRecords, filters),
    logicFailureSummary: filterRows(raw.logicFailureSummary, filters),
    diagnosisTimeline: raw.diagnosisTimeline,
    failureCorrelation: raw.failureCorrelation,
    coverageCorrelation: raw.coverageCorrelation,
    diagnosisReports: filterRows(raw.diagnosisReports, filters),
    affectedLogicBlocks: filterRows(raw.affectedLogicBlocks, filters),
    debugRecommendations: filterRows(raw.debugRecommendations, filters),
    aiRecommendations: filterRows(raw.aiRecommendations, filters),
    riskCards: raw.riskCards,
    generateCoverageHeatmap: wrapHeatmapGenerator(raw.generateCoverageHeatmap, filters),
    connectivityNodes: raw.connectivityNodes,
  };
}

function applyLbistLive(
  base: ReturnType<typeof buildFilteredLbistData>,
  api: DashboardTabData,
  tab: string,
  filters: GlobalFilters
) {
  const kpis = (api.kpis ?? []) as typeof raw.overviewKPIs;
  const rows = filterRows((api.rows ?? []) as Record<string, unknown>[], filters);
  switch (tab) {
    case "coverage-analysis":
      return { ...base, coverageKPIs: kpis, recentFailures: rows as unknown as typeof raw.recentFailures };
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

export function useFilteredLbistData() {
  const mockBuilder = useCallback((filters: GlobalFilters) => buildFilteredLbistData(filters), []);
  return useModuleDashboard("lbist", mockBuilder, [...CHART_KEYS], applyLbistLive, (tab, filters) =>
    getModuleTab("lbist", tab, filters)
  );
}

export type FilteredLbistData = ReturnType<typeof useFilteredLbistData>;
