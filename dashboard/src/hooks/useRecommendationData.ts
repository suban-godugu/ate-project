"use client";

import { useCallback } from "react";
import * as raw from "@/lib/recommendationData";
import { getRecommendationAgent } from "@/lib/api/dashboard";
import { useModuleDashboard } from "@/hooks/useModuleDashboard";
import {
  filterKPIArray,
  filterKPISections,
  filterRows,
  wrapHeatmapGenerator,
} from "@/hooks/dataFilterUtils";
import type { GlobalFilters } from "@/types/platform";
import type { DashboardTabData } from "@/lib/api/dashboard";

const CHART_KEYS = [
  "priorityDistribution",
  "sourceDistribution",
  "recommendationTrend",
  "patternRecDistribution",
  "patternCoverageTrend",
  "rootCauseDistribution",
  "debugPriorityData",
  "failureCorrelationTrend",
  "yieldImprovementTrend",
  "costReductionTrend",
  "testTimeTrend",
  "roiAnalysisTrend",
  "adaptiveTestingDistribution",
  "optimizationPriorityData",
  "testOptRecommendationTrend",
] as const;

function buildFilteredRecommendationData(filters: GlobalFilters) {
  return {
    overviewKPIs: filterKPIArray(raw.overviewKPIs, filters),
    scanChainKPIs: filterKPIArray(raw.scanChainKPIs, filters),
    mbistKPIs: filterKPIArray(raw.mbistKPIs, filters),
    lbistKPIs: filterKPIArray(raw.lbistKPIs, filters),
    waferKPIs: filterKPIArray(raw.waferKPIs, filters),
    sourceDistribution: raw.sourceDistribution,
    priorityDistribution: raw.priorityDistribution,
    recommendationTrend: raw.recommendationTrend,
    unifiedRecommendations: filterRows(raw.unifiedRecommendations, filters),
    aiExecutiveSummary: raw.aiExecutiveSummary,
    scanChainRecommendations: filterRows(raw.scanChainRecommendations, filters),
    mbistRecommendations: filterRows(raw.mbistRecommendations, filters),
    lbistRecommendations: filterRows(raw.lbistRecommendations, filters),
    waferRecommendations: filterRows(raw.waferRecommendations, filters),
    bottomAISummary: raw.bottomAISummary,
    scanFailureTrend: raw.scanFailureTrend,
    chainHealthTrend: raw.chainHealthTrend,
    memoryFailureTrend: raw.memoryFailureTrend,
    coverageTrendLbist: raw.coverageTrendLbist,
    waferYieldTrend: raw.waferYieldTrend,
    generateWaferRecHeatmap: wrapHeatmapGenerator(raw.generateWaferRecHeatmap, filters),
    workflowSteps: raw.workflowSteps,
    centerKPIs: filterKPIArray(raw.centerKPIs, filters),
    patternAgentMeta: raw.patternAgentMeta,
    scanDebugAgentMeta: raw.scanDebugAgentMeta,
    testOptAgentMeta: raw.testOptAgentMeta,
    patternRecDistribution: raw.patternRecDistribution,
    patternCoverageTrend: raw.patternCoverageTrend,
    patternRecRows: filterRows(raw.patternRecRows, filters),
    rootCauseDistribution: raw.rootCauseDistribution,
    debugPriorityData: raw.debugPriorityData,
    failureCorrelationTrend: raw.failureCorrelationTrend,
    scanDebugRecRows: filterRows(raw.scanDebugRecRows, filters),
    affectedScanChainsData: raw.affectedScanChainsData,
    yieldImprovementTrend: raw.yieldImprovementTrend,
    costReductionTrend: raw.costReductionTrend,
    testTimeTrend: raw.testTimeTrend,
    testOptRecRows: filterRows(raw.testOptRecRows, filters),
    roiAnalysisTrend: raw.roiAnalysisTrend,
    powerSavingTrend: raw.powerSavingTrend,
    patternClusterData: raw.patternClusterData,
    patternAgentKPIs: filterKPIArray(raw.patternAgentKPIs, filters),
    scanDebugAgentKPIs: filterKPIArray(raw.scanDebugAgentKPIs, filters),
    scanDebugKPISections: filterKPISections(raw.scanDebugKPISections, filters),
    failureRootCauseDistribution: raw.failureRootCauseDistribution,
    debugRecommendationPriority: raw.debugRecommendationPriority,
    scanDebugRecommendationTrend: raw.scanDebugRecommendationTrend,
    scanDebugWorkflowSteps: raw.scanDebugWorkflowSteps,
    testOptAgentKPIs: filterKPIArray(raw.testOptAgentKPIs, filters),
    testOptKPISections: filterKPISections(raw.testOptKPISections, filters),
    adaptiveTestingDistribution: raw.adaptiveTestingDistribution,
    optimizationPriorityData: raw.optimizationPriorityData,
    testOptRecommendationTrend: raw.testOptRecommendationTrend,
    testOptWorkflowSteps: raw.testOptWorkflowSteps,
    generateSiteUtilizationHeatmap: wrapHeatmapGenerator(raw.generateSiteUtilizationHeatmap, filters),
    patternAgentSummary: raw.patternAgentSummary,
    scanDebugAgentSummary: raw.scanDebugAgentSummary,
    testOptAgentSummary: raw.testOptAgentSummary,
    enterpriseExecutiveSummary: raw.enterpriseExecutiveSummary,
    agentWorkflowSteps: raw.agentWorkflowSteps,
  };
}

function applyRecommendationLive(
  base: ReturnType<typeof buildFilteredRecommendationData>,
  api: DashboardTabData,
  tab: string,
  filters: GlobalFilters
) {
  const kpis = (api.kpis ?? []) as typeof raw.overviewKPIs;
  const rows = filterRows((api.rows ?? []) as Record<string, unknown>[], filters);
  switch (tab) {
    case "pattern-agent":
      return {
        ...base,
        patternAgentKPIs: kpis as typeof raw.patternAgentKPIs,
        patternRecRows: rows as unknown as typeof raw.patternRecRows,
      };
    case "scan-debug-agent":
      return {
        ...base,
        scanDebugAgentKPIs: kpis as typeof raw.scanDebugAgentKPIs,
        scanDebugRecRows: rows as unknown as typeof raw.scanDebugRecRows,
      };
    case "test-optimization-agent":
      return {
        ...base,
        testOptAgentKPIs: kpis as typeof raw.testOptAgentKPIs,
        testOptRecRows: rows as unknown as typeof raw.testOptRecRows,
      };
    case "overview":
    default:
      return {
        ...base,
        overviewKPIs: kpis,
        unifiedRecommendations: rows as unknown as typeof raw.unifiedRecommendations,
      };
  }
}

export function useFilteredRecommendationData() {
  const mockBuilder = useCallback(
    (filters: GlobalFilters) => buildFilteredRecommendationData(filters),
    []
  );
  return useModuleDashboard(
    "recommendation-analysis",
    mockBuilder,
    [...CHART_KEYS],
    applyRecommendationLive,
    getRecommendationAgent
  );
}

export type FilteredRecommendationData = ReturnType<typeof useFilteredRecommendationData>;
