"use client";

import { useCallback } from "react";
import * as raw from "@/lib/costIntelligenceData";
import { getCostIntelligence } from "@/lib/api/dashboard";
import { useModuleDashboard } from "@/hooks/useModuleDashboard";
import { filterKPIArray, filterRows, wrapHeatmapGenerator } from "@/hooks/dataFilterUtils";
import { heatmapFromCells } from "@/lib/api/mergeLiveDashboard";
import type { GlobalFilters } from "@/types/platform";
import type { DashboardTabData } from "@/lib/api/dashboard";
import type { AICostSummary, EnterpriseCostSummary, ModuleCostSummary } from "@/types/costIntelligence";

const CHART_KEYS = [
  "costContribution",
  "costBreakdown",
  "costDistribution",
  "monthlyCostTrend",
  "patternCostTrend",
  "memoryCostTrend",
  "logicCostTrend",
  "waferCostTrend",
  "projectedSavings",
  "defectDensityCost",
  "yieldBinDistribution",
  "waferCostHeatmap",
] as const;

const EMPTY_AI_COST_SUMMARY: AICostSummary = {
  highestCostModule: "—",
  mostExpensivePattern: "—",
  longestTestTime: "—",
  highestRetestCost: "—",
  highestRepairCost: "—",
  estimatedSavings: "—",
};

const EMPTY_ENTERPRISE_COST_SUMMARY: EnterpriseCostSummary = {
  modules: [],
  totalCost: "—",
  totalSavings: "—",
  roi: "—",
  yieldImprovement: "—",
  testTimeReduction: "—",
};

function asDisplayString(value: unknown, fallback = "—"): string {
  return typeof value === "string" && value.length > 0 ? value : fallback;
}

/** Backend may return {} when no cost facts exist — never leave modules undefined. */
function normalizeEnterpriseCostSummary(value: unknown): EnterpriseCostSummary {
  if (!value || typeof value !== "object") return EMPTY_ENTERPRISE_COST_SUMMARY;
  const o = value as Record<string, unknown>;
  const modules = Array.isArray(o.modules)
    ? (o.modules.filter(
        (m): m is ModuleCostSummary =>
          !!m && typeof m === "object" && typeof (m as ModuleCostSummary).module === "string"
      ) as ModuleCostSummary[])
    : [];
  return {
    modules,
    totalCost: asDisplayString(o.totalCost),
    totalSavings: asDisplayString(o.totalSavings),
    roi: asDisplayString(o.roi),
    yieldImprovement: asDisplayString(o.yieldImprovement),
    testTimeReduction: asDisplayString(o.testTimeReduction),
  };
}

function normalizeAICostSummary(value: unknown): AICostSummary {
  if (!value || typeof value !== "object") return EMPTY_AI_COST_SUMMARY;
  const o = value as Record<string, unknown>;
  if (Object.keys(o).length === 0) return EMPTY_AI_COST_SUMMARY;
  return {
    highestCostModule: asDisplayString(o.highestCostModule),
    mostExpensivePattern: asDisplayString(o.mostExpensivePattern),
    longestTestTime: asDisplayString(o.longestTestTime),
    highestRetestCost: asDisplayString(o.highestRetestCost),
    highestRepairCost: asDisplayString(o.highestRepairCost),
    estimatedSavings: asDisplayString(o.estimatedSavings),
  };
}

function chartExtras(api: DashboardTabData) {
  const charts = api.charts ?? {};
  return {
    aiCostSummary: normalizeAICostSummary(charts.aiCostSummary),
    enterpriseCostSummary: normalizeEnterpriseCostSummary(charts.enterpriseCostSummary),
  };
}

function buildFilteredCostIntelligenceData(filters: GlobalFilters) {
  return {
    overviewKPIs: filterKPIArray(raw.overviewKPIs, filters),
    scanChainKPIs: filterKPIArray(raw.scanChainKPIs, filters),
    mbistKPIs: filterKPIArray(raw.mbistKPIs, filters),
    lbistKPIs: filterKPIArray(raw.lbistKPIs, filters),
    waferKPIs: filterKPIArray(raw.waferKPIs, filters),
    costContribution: raw.costContribution,
    costBreakdown: raw.costBreakdown,
    monthlyCostTrend: raw.monthlyCostTrend,
    costDistribution: raw.costDistribution,
    productCostRows: filterRows(raw.productCostRows, filters),
    aiCostSummary: raw.aiCostSummary,
    scanChainCostRows: filterRows(raw.scanChainCostRows, filters),
    mbistCostRows: filterRows(raw.mbistCostRows, filters),
    lbistCostRows: filterRows(raw.lbistCostRows, filters),
    waferCostRows: filterRows(raw.waferCostRows, filters),
    aiCostRecommendations: filterRows(raw.aiCostRecommendations, filters),
    enterpriseCostSummary: raw.enterpriseCostSummary,
    patternCostTrend: raw.patternCostTrend,
    memoryCostTrend: raw.memoryCostTrend,
    logicCostTrend: raw.logicCostTrend,
    waferCostTrend: raw.waferCostTrend,
    defectDensityCost: [
      { label: "Zone A", value: 12.4 },
      { label: "Zone B", value: 18.6 },
      { label: "Zone C", value: 14.2 },
      { label: "Zone D", value: 22.8 },
    ],
    yieldBinDistribution: [
      { name: "Pass", value: 62, color: "#22C55E" },
      { name: "Fail", value: 38, color: "#EF4444" },
    ],
    generateWaferCostHeatmap: wrapHeatmapGenerator(raw.generateWaferCostHeatmap, filters),
  };
}

function applyCostLive(
  base: ReturnType<typeof buildFilteredCostIntelligenceData>,
  api: DashboardTabData,
  tab: string,
  filters: GlobalFilters
) {
  const kpis = (api.kpis ?? []) as typeof raw.overviewKPIs;
  const rows = filterRows((api.rows ?? []) as Record<string, unknown>[], filters);
  const tabMap: Record<string, { kpi: keyof typeof base; row: keyof typeof base }> = {
    "scan-chain": { kpi: "scanChainKPIs", row: "scanChainCostRows" },
    mbist: { kpi: "mbistKPIs", row: "mbistCostRows" },
    lbist: { kpi: "lbistKPIs", row: "lbistCostRows" },
    wafer: { kpi: "waferKPIs", row: "waferCostRows" },
    "ai-optimization": { kpi: "overviewKPIs", row: "aiCostRecommendations" },
  };
  if (tab === "overview") {
    const charts = api.charts ?? {};
    const liveHeatmap = heatmapFromCells(
      charts.waferCostHeatmap as { row: number; col: number; value: number }[] | undefined,
      12,
      16
    );
    return {
      ...base,
      overviewKPIs: kpis,
      productCostRows: rows as unknown as typeof raw.productCostRows,
      generateWaferCostHeatmap: liveHeatmap.length > 0 ? () => liveHeatmap : base.generateWaferCostHeatmap,
      ...chartExtras(api),
    };
  }
  const mapped = tabMap[tab];
  const charts = api.charts ?? {};
  const liveHeatmap = heatmapFromCells(
    charts.waferCostHeatmap as { row: number; col: number; value: number }[] | undefined,
    12,
    16
  );
  const heatmapGenerator =
    liveHeatmap.length > 0
      ? () => liveHeatmap
      : base.generateWaferCostHeatmap;

  if (mapped) {
    return {
      ...base,
      [mapped.kpi]: kpis,
      [mapped.row]: rows,
      generateWaferCostHeatmap: heatmapGenerator,
      ...chartExtras(api),
    };
  }
  return { ...base, generateWaferCostHeatmap: heatmapGenerator, ...chartExtras(api) };
}

export function useFilteredCostIntelligenceData() {
  const mockBuilder = useCallback(
    (filters: GlobalFilters) => buildFilteredCostIntelligenceData(filters),
    []
  );
  return useModuleDashboard(
    "cost-intelligence",
    mockBuilder,
    [...CHART_KEYS],
    applyCostLive,
    getCostIntelligence
  );
}

export type FilteredCostIntelligenceData = ReturnType<typeof useFilteredCostIntelligenceData>;
