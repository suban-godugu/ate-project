"use client";

import { useCallback } from "react";
import * as raw from "@/lib/scanChainData";
import { getModuleTab } from "@/lib/api/dashboard";
import { heatmapFromCells } from "@/lib/api/mergeLiveDashboard";
import { useModuleDashboard } from "@/hooks/useModuleDashboard";
import {
  filterHeatmapGrid,
  filterKPIArray,
  filterKPISections,
  filterRows,
  wrapHeatmapGenerator,
} from "@/hooks/dataFilterUtils";
import type { GlobalFilters } from "@/types/platform";
import type { DashboardTabData } from "@/lib/api/dashboard";

const ALL_CHART_KEYS = [
  "chainHealthData",
  "failureDistribution",
  "failureTrendData",
  "topFailingChips",
  "failureAnalysisDistribution",
  "overallFailureTrend",
  "failureRateTrend",
  "patternImportTrend",
  "patternClusterDistribution",
  "patternAnalysisCoverageTrend",
  "patternFrequency",
  "patternLengthDistribution",
  "patternGrowthTrend",
  "rootCauseFrequency",
  "recurringFailureTrend",
  "criticalChainDistribution",
  "chainFailureRanking",
  "failureByLotData",
  "diagnosisTimeline",
  "aiConfidenceTrend",
  "failureLocalizationDistribution",
  "diagnosisConfidenceTrend30Day",
] as const;

function buildFilteredScanChainData(filters: GlobalFilters) {
  return {
    overviewKPIs: filterKPIArray(raw.overviewKPIs, filters),
    patternKPIs: filterKPIArray(raw.patternKPIs, filters),
    failureKPIs: filterKPIArray(raw.failureKPIs, filters),
    diagnosisKPIs: filterKPIArray(raw.diagnosisKPIs, filters),
    chainHealthData: raw.chainHealthData,
    topFailingChips: filterRows(raw.topFailingChips, filters),
    failingChainsData: filterRows(raw.failingChainsData, filters),
    failureDistribution: raw.failureDistribution,
    aiDiagnosisSummary: raw.aiDiagnosisSummary,
    patternExecutionTrend: raw.patternExecutionTrend,
    patternCostTrend: raw.patternCostTrend,
    patternCoverageTrend: raw.patternCoverageTrend,
    patternDensityData: raw.patternDensityData,
    patternSummaryData: filterRows(raw.patternSummaryData, filters),
    patternRecommendations: filterRows(raw.patternRecommendations, filters),
    patternAnalysisKPIs: filterKPIArray(raw.patternAnalysisKPIs, filters),
    patternImportTrend: raw.patternImportTrend,
    patternAnalysisCoverageTrend: raw.patternAnalysisCoverageTrend,
    patternClusterDistribution: raw.patternClusterDistribution,
    patternScatterData: filterRows(raw.patternScatterData, filters),
    patternAnalysisRows: filterRows(raw.patternAnalysisRows, filters),
    patternAISummary: raw.patternAISummary,
    patternRedundancyHeatmap: filterHeatmapGrid(raw.patternRedundancyHeatmap, filters),
    patternSimilarityMatrix: filterHeatmapGrid(raw.patternSimilarityMatrix, filters),
    failureTrendData: raw.failureTrendData,
    failingRegionsData: raw.failingRegionsData,
    failureDensityData: raw.failureDensityData,
    failureRecords: filterRows(raw.failureRecords, filters),
    rootCauseAnalysis: filterRows(raw.rootCauseAnalysis, filters),
    aiRecommendations: filterRows(raw.aiRecommendations, filters),
    diagnosisTimeline: raw.diagnosisTimeline,
    aiConfidenceTrend: raw.aiConfidenceTrend,
    diagnosisReports: filterRows(raw.diagnosisReports, filters),
    suspectedScanCells: filterRows(raw.suspectedScanCells, filters),
    debugPoints: filterRows(raw.debugPoints, filters),
    repairPriorityData: filterRows(raw.repairPriorityData, filters),
    generateScanChainHeatmap: wrapHeatmapGenerator(raw.generateScanChainHeatmap, filters),
    connectivityGraphData: raw.connectivityGraphData,
    failurePropagationData: raw.failurePropagationData,
    failureAnalysisKPIs: filterKPIArray(raw.failureAnalysisKPIs, filters),
    overallFailureTrend: raw.overallFailureTrend,
    failureRateTrend: raw.failureRateTrend,
    failureAnalysisDistribution: raw.failureAnalysisDistribution,
    failureByLotData: filterRows(raw.failureByLotData, filters),
    failureAnalysisRows: filterRows(raw.failureAnalysisRows, filters),
    failureCorrelationMatrix: filterHeatmapGrid(raw.failureCorrelationMatrix, filters),
    failureCorrelationLabels: raw.failureCorrelationLabels,
    failureRootCauseTree: raw.failureRootCauseTree,
    failureAISummary: raw.failureAISummary,
    generateWaferFailureHeatmap: wrapHeatmapGenerator(raw.generateWaferFailureHeatmap, filters),
    generateDieFailureHeatmap: wrapHeatmapGenerator(raw.generateDieFailureHeatmap, filters),
    scanDiagnosisKPISections: filterKPISections(raw.scanDiagnosisKPISections, filters),
    failureLocalizationDistribution: raw.failureLocalizationDistribution,
    chainFailureRanking: filterRows(raw.chainFailureRanking, filters),
    diagnosisConfidenceTrend30Day: raw.diagnosisConfidenceTrend30Day,
    scanTopologyGraphData: raw.scanTopologyGraphData,
    scanDiagnosisCorrelationMatrix: raw.scanDiagnosisCorrelationMatrix,
    scanDiagnosisRecommendationRows: filterRows(raw.scanDiagnosisRecommendationRows, filters),
    scanDiagnosisExecutiveSummary: raw.scanDiagnosisExecutiveSummary,
    scanDiagnosisWorkflowSteps: raw.scanDiagnosisWorkflowSteps,
  };
}

function applyScanChainLive(
  base: ReturnType<typeof buildFilteredScanChainData>,
  api: DashboardTabData,
  tab: string,
  filters: GlobalFilters
) {
  const kpis = (api.kpis ?? []) as typeof raw.overviewKPIs;
  const rows = filterRows((api.rows ?? []) as Record<string, unknown>[], filters);
  const cells = api.charts?.heatmapCells as { row: number; col: number; value: number }[] | undefined;
  const heatmap =
    cells?.length
      ? { generateScanChainHeatmap: (r = 12, c = 12) => heatmapFromCells(cells, r, c) }
      : {};

  switch (tab) {
    case "pattern-analysis":
      return {
        ...base,
        patternAnalysisKPIs: kpis as unknown as typeof raw.patternAnalysisKPIs,
        patternAnalysisRows: rows as unknown as typeof raw.patternAnalysisRows,
      };
    case "failure-analysis":
      return {
        ...base,
        failureAnalysisKPIs: kpis as unknown as typeof raw.failureAnalysisKPIs,
        failureAnalysisRows: rows as unknown as typeof raw.failureAnalysisRows,
        failureRecords: rows as unknown as typeof raw.failureRecords,
      };
    case "scan-diagnosis":
      return {
        ...base,
        diagnosisKPIs: kpis,
        scanDiagnosisRecommendationRows: rows as unknown as typeof raw.scanDiagnosisRecommendationRows,
        chainFailureRanking: rows as unknown as typeof raw.chainFailureRanking,
      };
    default:
      return {
        ...base,
        overviewKPIs: kpis,
        failingChainsData: rows as unknown as typeof raw.failingChainsData,
        ...heatmap,
      };
  }
}

export function useFilteredScanChainData() {
  const mockBuilder = useCallback((filters: GlobalFilters) => buildFilteredScanChainData(filters), []);
  return useModuleDashboard(
    "scan-chain",
    mockBuilder,
    [...ALL_CHART_KEYS] as unknown as (keyof ReturnType<typeof buildFilteredScanChainData>)[],
    applyScanChainLive,
    (tab, filters) => getModuleTab("scan-chain", tab, filters)
  );
}

export type FilteredScanChainData = ReturnType<typeof useFilteredScanChainData>;
