import type { DrillDownKPI } from "@/types/kpiDrillDown";
import type {
  KpiBreakdownSlice,
  KpiDrillDownFilters,
  KpiExecutiveSummaryCard,
  KpiRecommendation,
  KpiRelatedModule,
  KpiRootCause,
  KpiSemiconductorMeta,
  KpiTableRow,
  KpiTimelineEvent,
  KpiTrendAnalytics,
  KpiTrendTab,
  KpiWorkspaceData,
  KpiWorkspaceFooter,
  KpiWorkspaceHeader,
  KpiRiskLevel,
  KpiAiDecisionOverview,
  KpiAiExplanation,
  KpiExpectedImpactCard,
  KpiImpactMetric,
  KpiApprovalAction,
} from "@/types/kpiDrillDown";
import { KPI_BREAKDOWN_DIMENSIONS, FAILURE_BREAKDOWN_DIMENSIONS, DIAGNOSIS_BREAKDOWN_DIMENSIONS, RECOMMENDATION_BREAKDOWN_DIMENSIONS, TEST_OPT_BREAKDOWN_DIMENSIONS, SCAN_DEBUG_BREAKDOWN_DIMENSIONS, DIAGNOSIS_TREND_TABS, KPI_TREND_TABS } from "@/types/kpiDrillDown";
import type { KpiTopologyEdge, KpiTopologyNode, KpiTraceabilityNode } from "@/types/kpiDrillDown";
import { buildWidgetSpecs, getKpiProfile } from "@/lib/kpiDrillDown/kpiProfiles";
import {
  DEFAULT_COPILOT_SUGGESTIONS,
  DIAGNOSIS_COPILOT_SUGGESTIONS,
  FAILURE_COPILOT_SUGGESTIONS,
  isFailureAnalysisKpi,
  isPatternAnalysisKpi,
  isScanDiagnosisKpi,
  isPatternAgentKpi,
  isTestOptAgentKpi,
  isScanDebugAgentKpi,
  isOptimizationAgentKpi,
  isRecommendationAgentKpi,
  topologyFirstKpi,
  workspaceLayoutPreset,
  workspaceModule,
  RECOMMENDATION_COPILOT_SUGGESTIONS,
  TEST_OPT_COPILOT_SUGGESTIONS,
  SCAN_DEBUG_COPILOT_SUGGESTIONS,
} from "@/lib/kpiDrillDown/kpiDrillDownUtils";

function hashSeed(str: string): number {
  let h = 0;
  for (let i = 0; i < str.length; i++) h = (h << 5) - h + str.charCodeAt(i);
  return Math.abs(h);
}

function rnd(seed: number, i: number): number {
  const x = Math.sin(seed + i * 9999) * 10000;
  return x - Math.floor(x);
}

function parseNum(raw: string): number {
  const m = raw.replace(/,/g, "").match(/[\d.]+/);
  return m ? parseFloat(m[0]) : 0;
}

function riskFromChange(change: number, positiveIsGood: boolean): KpiRiskLevel {
  const bad = positiveIsGood ? change < -3 : change > 3;
  if (Math.abs(change) > 8 && bad) return "critical";
  if (bad) return "high";
  if ((positiveIsGood ? change < 0 : change > 0)) return "medium";
  return "nominal";
}

function sparkline(seed: number, base: number, len = 7): number[] {
  return Array.from({ length: len }, (_, i) =>
    Math.round(base * (0.88 + rnd(seed, i) * 0.2))
  );
}

function buildExecutiveSummary(kpi: DrillDownKPI, seed: number): KpiExecutiveSummaryCard[] {
  const base = parseNum(kpi.value) || 50;
  const target = base * (kpi.positiveIsGood ? 1.02 : 0.96);
  const delta = base - target;
  const riskLevel = riskFromChange(kpi.change, kpi.positiveIsGood ?? true);

  if (isFailureAnalysisKpi(kpi.id)) {
    return [
      { id: "current", label: "Current KPI", value: kpi.value, icon: "gauge", sparkline: kpi.sparkline.length ? kpi.sparkline : sparkline(seed, base) },
      { id: "target", label: "Target", value: `${target.toFixed(2)}${kpi.value.includes("%") ? "%" : ""}`, icon: "target", sparkline: sparkline(seed + 1, target) },
      { id: "delta", label: "Delta", value: `${delta >= 0 ? "+" : ""}${delta.toFixed(2)}`, icon: "git-compare", sparkline: sparkline(seed + 2, Math.abs(delta)), variant: delta >= 0 ? "success" : "danger" },
      { id: "trend", label: "Trend", value: `${kpi.change >= 0 ? "+" : ""}${kpi.change}%`, icon: kpi.trend === "up" ? "trending-up" : "trending-down", sparkline: kpi.sparkline, variant: kpi.trend === "up" && !kpi.positiveIsGood ? "danger" : "success" },
      { id: "risk", label: "Risk", value: riskLevel.charAt(0).toUpperCase() + riskLevel.slice(1), icon: "alert-triangle", sparkline: sparkline(seed + 3, 68), variant: riskLevel === "critical" || riskLevel === "high" ? "danger" : "warning" },
      { id: "business", label: "Business Impact", value: rnd(seed, 3) > 0.55 ? "Fab Escalation" : "Line Monitor", icon: "briefcase", sparkline: sparkline(seed + 4, 72), variant: "warning" },
      { id: "yield", label: "Yield Impact", value: `-${(rnd(seed, 5) * 1.4 + 0.2).toFixed(2)}%`, icon: "trending-down", sparkline: sparkline(seed + 5, 42), variant: "danger" },
      { id: "cost", label: "Cost Impact", value: `$${Math.round(rnd(seed, 6) * 42000 + 8000).toLocaleString()}`, icon: "dollar-sign", sparkline: sparkline(seed + 6, 58), variant: "info" },
    ];
  }

  if (isPatternAgentKpi(kpi.id)) {
    return [
      { id: "current", label: "Current Value", value: kpi.value, icon: "gauge", sparkline: kpi.sparkline.length ? kpi.sparkline : sparkline(seed, base) },
      { id: "target", label: "Target", value: kpi.id === "coverage-delta" ? "99.5%" : "Optimized", icon: "target", sparkline: sparkline(seed + 1, target) },
      { id: "pattern-red", label: "Pattern Reduction", value: "-28", icon: "copy", sparkline: sparkline(seed + 2, 28), variant: "success" },
      { id: "cov-gain", label: "Coverage Gain", value: "+1.2%", icon: "trending-up", sparkline: sparkline(seed + 3, 12), variant: "success" },
      { id: "runtime", label: "Runtime Reduction", value: "-12.4%", icon: "clock-3", sparkline: sparkline(seed + 4, 12), variant: "success" },
      { id: "power", label: "Power Saving", value: "21.6%", icon: "zap-off", sparkline: sparkline(seed + 5, 22), variant: "success" },
      { id: "memory", label: "Memory Saving", value: "-18%", icon: "hard-drive", sparkline: sparkline(seed + 6, 18), variant: "info" },
      { id: "cost", label: "ATE Cost Saving", value: "$48K", icon: "dollar-sign", sparkline: sparkline(seed + 7, 48), variant: "success" },
      { id: "roi", label: "Business ROI", value: "3.8x", icon: "briefcase", sparkline: sparkline(seed + 8, 38), variant: "success" },
    ];
  }

  if (isTestOptAgentKpi(kpi.id)) {
    return [
      { id: "current", label: "Current Value", value: kpi.value, icon: "gauge", sparkline: kpi.sparkline.length ? kpi.sparkline : sparkline(seed, base) },
      { id: "target", label: "Target", value: kpi.id === "projected-yield" ? "90.5%" : "Optimized", icon: "target", sparkline: sparkline(seed + 1, target) },
      { id: "gain", label: "Expected Gain", value: kpi.id === "test-time-red" ? "18%" : kpi.id === "projected-yield" ? "+3.1%" : "+12.4%", icon: "trending-up", sparkline: sparkline(seed + 2, 12), variant: "success" },
      { id: "yield", label: "Yield Improvement", value: "+3.1%", icon: "target", sparkline: sparkline(seed + 3, 31), variant: "success" },
      { id: "cost", label: "Cost Saving", value: "$48K", icon: "dollar-sign", sparkline: sparkline(seed + 4, 48), variant: "success" },
      { id: "runtime", label: "Runtime Saving", value: "-18%", icon: "clock-3", sparkline: sparkline(seed + 5, 18), variant: "success" },
      { id: "power", label: "Power Saving", value: "14.2%", icon: "zap-off", sparkline: sparkline(seed + 6, 14), variant: "success" },
      { id: "roi", label: "ROI", value: "4.2x", icon: "briefcase", sparkline: sparkline(seed + 7, 42), variant: "success" },
      { id: "business", label: "Business Impact", value: rnd(seed, 8) > 0.5 ? "High Priority" : "Production Ready", icon: "factory", sparkline: sparkline(seed + 8, 72), variant: "warning" },
    ];
  }

  if (isScanDebugAgentKpi(kpi.id)) {
    return [
      { id: "current", label: "Current KPI", value: kpi.value, icon: "gauge", sparkline: kpi.sparkline.length ? kpi.sparkline : sparkline(seed, base) },
      { id: "target", label: "Target", value: kpi.id === "avg-confidence" || kpi.id === "defect-localization" ? "95%" : "Resolved", icon: "target", sparkline: sparkline(seed + 1, target) },
      { id: "rec-count", label: "Recommendation Count", value: String(Math.round(8 + rnd(seed, 2) * 14)), icon: "clipboard-list", sparkline: sparkline(seed + 2, 14), variant: "info" },
      { id: "chains", label: "Affected Chains", value: "7", icon: "unplug", sparkline: sparkline(seed + 3, 7), variant: "danger" },
      { id: "patterns", label: "Affected Patterns", value: "12", icon: "alert-triangle", sparkline: sparkline(seed + 4, 12), variant: "warning" },
      { id: "wafers", label: "Affected Wafers", value: "4", icon: "disc", sparkline: sparkline(seed + 5, 4), variant: "warning" },
      { id: "lots", label: "Affected Lots", value: "3", icon: "layers", sparkline: sparkline(seed + 6, 3), variant: "info" },
      { id: "cov-gain", label: "Coverage Gain", value: "+1.8%", icon: "trending-up", sparkline: sparkline(seed + 7, 18), variant: "success" },
      { id: "runtime", label: "Runtime Saving", value: "-8.4%", icon: "clock-3", sparkline: sparkline(seed + 8, 8), variant: "success" },
      { id: "power", label: "Power Saving", value: "12.6%", icon: "zap-off", sparkline: sparkline(seed + 9, 13), variant: "success" },
      { id: "cost", label: "ATE Cost Saving", value: "$22K", icon: "dollar-sign", sparkline: sparkline(seed + 10, 22), variant: "success" },
      { id: "business", label: "Business Impact", value: rnd(seed, 11) > 0.5 ? "Hold Lot" : "Debug Priority", icon: "briefcase", sparkline: sparkline(seed + 11, 62), variant: "warning" },
    ];
  }

  if (isScanDiagnosisKpi(kpi.id)) {
    return [
      { id: "current", label: "Current KPI", value: kpi.value, icon: "gauge", sparkline: kpi.sparkline.length ? kpi.sparkline : sparkline(seed, base) },
      { id: "target", label: "Target", value: kpi.id === "sd-avg-confidence" ? "95%" : `${Math.max(0, base * 0.85).toFixed(0)}`, icon: "target", sparkline: sparkline(seed + 1, target) },
      { id: "chains", label: "Affected Chains", value: "14", icon: "unplug", sparkline: sparkline(seed + 2, 14), variant: "danger" },
      { id: "patterns", label: "Affected Patterns", value: "8", icon: "alert-triangle", sparkline: sparkline(seed + 3, 8), variant: "warning" },
      { id: "wafers", label: "Affected Wafers", value: "5", icon: "disc", sparkline: sparkline(seed + 4, 5), variant: "warning" },
      { id: "lots", label: "Affected Lots", value: "3", icon: "layers", sparkline: sparkline(seed + 5, 3), variant: "info" },
      { id: "confidence", label: "Diagnosis Confidence", value: "91%", icon: "shield-check", sparkline: sparkline(seed + 6, 91), variant: "success" },
      { id: "yield", label: "Est. Yield Loss", value: `-${(rnd(seed, 7) * 0.9 + 0.15).toFixed(2)}%`, icon: "trending-down", sparkline: sparkline(seed + 7, 38), variant: "danger" },
      { id: "business", label: "Business Impact", value: rnd(seed, 8) > 0.5 ? "Hold Lot" : "Debug Priority", icon: "briefcase", sparkline: sparkline(seed + 8, 62), variant: "warning" },
      { id: "trend", label: "Trend", value: `${kpi.change >= 0 ? "+" : ""}${kpi.change}%`, icon: kpi.trend === "up" ? "trending-up" : "trending-down", sparkline: kpi.sparkline, variant: kpi.positiveIsGood ? "success" : "danger" },
    ];
  }

  return [
    { id: "current", label: "Current Value", value: kpi.value, icon: "gauge", sparkline: kpi.sparkline.length ? kpi.sparkline : sparkline(seed, base) },
    { id: "target", label: "Target Value", value: `${target.toFixed(1)}${kpi.value.includes("%") ? "%" : ""}`, icon: "target", sparkline: sparkline(seed + 1, target) },
    { id: "delta", label: "Delta", value: `${delta >= 0 ? "+" : ""}${delta.toFixed(1)}`, icon: "git-compare", sparkline: sparkline(seed + 2, Math.abs(delta)), variant: delta >= 0 ? "success" : "danger" },
    { id: "trend", label: "Trend", value: `${kpi.change >= 0 ? "+" : ""}${kpi.change}%`, icon: kpi.trend === "up" ? "trending-up" : "trending-down", sparkline: kpi.sparkline, variant: kpi.trend === "up" ? "success" : "warning" },
    { id: "business", label: "Business Impact", value: rnd(seed, 3) > 0.5 ? "High" : "Moderate", icon: "briefcase", sparkline: sparkline(seed + 3, 72), variant: "warning" },
    { id: "ops", label: "Operational Impact", value: rnd(seed, 4) > 0.6 ? "Fab Hold" : "Monitor", icon: "factory", sparkline: sparkline(seed + 4, 58), variant: "info" },
  ];
}

function buildTrendTab(tab: KpiTrendTab, kpi: DrillDownKPI, seed: number): KpiTrendAnalytics {
  const base = parseNum(kpi.value) || kpi.sparkline.at(-1) || 50;
  const points = tab === "24h" ? 24 : tab === "7d" ? 7 : tab === "30d" ? 30 : tab === "90d" ? 12 : 10;
  const series = Array.from({ length: points }, (_, i) => ({
    label:
      tab === "24h"
        ? `${i}:00`
        : tab === "prev-lot"
          ? i === 0
            ? "Current"
            : "Prev Lot"
          : tab === "prev-release"
            ? i % 2 === 0
              ? "Current"
              : "Prev Rel"
            : `P${i + 1}`,
    value: Math.round((base + (rnd(seed, i) - 0.5) * base * 0.1) * 10) / 10,
    value2: Math.round((base * 0.94 + (rnd(seed, i + 50) - 0.5) * base * 0.08) * 10) / 10,
  }));

  const chartKind: KpiTrendAnalytics["chartKind"] =
    tab === "prev-lot" || tab === "prev-release" ? "bar" : tab === "90d" ? "area" : "line";

  return {
    chartKind,
    series,
    comparisonLabel: tab === "prev-lot" ? "LOT-4418 baseline" : tab === "prev-release" ? "Release R3.1 baseline" : undefined,
  };
}

function buildRootCause(kpi: DrillDownKPI, filters: KpiDrillDownFilters, seed: number): KpiRootCause {
  const causes: Record<string, string> = {
    "overall-health": "Bridge fault clustering on high-fanout chains",
    "total-chains": "Module integration expanded chain inventory",
    "healthy-chains": "Repair actions restored chain integrity",
    "failing-chains": "Timing marginality at capture edge on T-104",
    "scan-coverage": "Redundant pattern removal reduced effective coverage",
    "avg-diagnosis-confidence": "Embedding model v2.4 improved localization",
    "avg-test-time": "Parallel scheduling reduced vector idle gaps",
    "files-ingested": "Batch STIL/WGL import from release R3.2 increased file volume",
    "vectors-parsed": "Parser v3.2.1 resolved edge-case WGL timing blocks",
    "file-integrity": "Checksum validation passed across all ingested sources",
    "pattern-coverage-kpi": "ATPG delta from redundant pattern pruning improved net coverage",
    "metadata-extracted": "Metadata schema v2 expanded flop and clock domain fields",
    "embeddings-generated": "Embedding pipeline batch completed for full pattern corpus",
    "pattern-clusters": "Similarity threshold 0.87 merged near-duplicate pattern families",
    "redundant-patterns": "Cluster analysis flagged 38 duplicate vectors for removal",
    "similarity-analyses": "GPU-accelerated cosine search reduced pairwise latency",
    "pass-fail-linked": "Historical fail log linkage improved for PAT-8821 family",
    "quality-reports": "Automated QA report generation triggered post-ingest validation",
    "imported-files": "STDF batch upload from LOT-A2847 increased ingest volume",
    "overall-failure-rate": "Bridge fault clustering elevated aggregate fail rate on T-104",
    "failing-patterns": "PAT-4821 and PAT-7892 dominate recurring at-speed failures",
    "die-failure-rate": "Edge die density shows elevated bridge signatures on W-042",
    "wafer-failure-rate": "Wafer W-051 edge ring correlates with handler alignment drift",
    "lot-failure-rate": "LOT-A2847 failure spike linked to program revision V3.2",
    "fault-categories": "Bridging faults increased share after metal layer change",
    "root-cause-confidence": "AI model v2.4 improved bridge fault localization confidence",
    "recurring-failures": "183 recurring signatures tracked across 37 production lots",
    "sd-failing-chains": "SC_14 bridge break at segment 4 — highest fanout chain",
    "sd-failing-cells": "73 scan cells flagged — SC_14-142 cluster density elevated",
    "sd-chain-breaks": "9 topology breaks detected between SC_14 and SC_08",
    "sd-shift-capture": "21 timing issues — 13 shift marginal, 8 capture edge failures",
    "sd-topology-chains": "128 chains loaded — 2 broken paths in M3-IO domain",
    "sd-chains-ranked": "SC_14 ranked #1 with 38 failures across 5 lots",
    "sd-failure-correlations": "61 correlated signatures link PAT-4821 to SC_14 family",
    "sd-top-failing-chain": "SC_14 failure history spans 5 lots with bridge signature",
    "sd-diagnosis-reports": "4 AI reports generated — 2 pending engineer sign-off",
    "sd-debug-locations": "31 debug locations mapped to wafer XY coordinates",
    "sd-avg-confidence": "AI model v2.4 improved localization to 91% average",
    "sd-pending-review": "6 diagnoses pending — 4 low confidence, 2 ambiguous root cause",
  };
  const severity = riskFromChange(kpi.change, kpi.positiveIsGood ?? true);
  const priorities: Array<"P0" | "P1" | "P2" | "P3"> = ["P0", "P1", "P2", "P3"];
  return {
    primaryCause: causes[kpi.id] ?? "Multi-factor tester site drift",
    confidence: Math.round(78 + rnd(seed, 10) * 18),
    affectedModules: ["M1-Core", "M3-IO", "M5-Cache"].slice(0, 2 + Math.floor(rnd(seed, 11) * 2)),
    affectedPatterns: ["PAT-4821", "PAT-7892", "PAT-3156"].slice(0, 1 + Math.floor(rnd(seed, 12) * 2)),
    affectedChains: ["SC-004821", "SC-007892", "SC-003156"].slice(0, 2 + Math.floor(rnd(seed, 13) * 1)),
    affectedLots: [filters.lot, "LOT-A2847", "LOT-B1923"].slice(0, 2 + Math.floor(rnd(seed, 14) * 1)),
    affectedWafers: [filters.wafer, "W-042", "W-051"].slice(0, 2 + Math.floor(rnd(seed, 15) * 1)),
    severity,
    risk: severity,
    priority: isFailureAnalysisKpi(kpi.id) ? priorities[Math.min(Math.floor(rnd(seed, 16) * 4), 3)] : undefined,
    expectedYieldImpact: isFailureAnalysisKpi(kpi.id)
      ? `-${(rnd(seed, 17) * 1.5 + 0.15).toFixed(2)}%`
      : `+${(rnd(seed, 14) * 1.2 + 0.3).toFixed(2)}%`,
    expectedCostImpact: isFailureAnalysisKpi(kpi.id)
      ? `$${Math.round(rnd(seed, 18) * 52000 + 12000).toLocaleString()}`
      : undefined,
    failureType: isScanDiagnosisKpi(kpi.id) ? "Chain Break / Bridge" : undefined,
    affectedScanCells: isScanDiagnosisKpi(kpi.id) ? ["SC_14-142", "SC_08-88", "SC_21-201"].slice(0, 2 + Math.floor(rnd(seed, 19) * 1)) : undefined,
    clockDomain: isScanDiagnosisKpi(kpi.id) ? "CLK_M3_FAST" : undefined,
    shiftCycle: isScanDiagnosisKpi(kpi.id) ? "Cycle 847" : undefined,
    captureCycle: isScanDiagnosisKpi(kpi.id) ? "Cycle 912" : undefined,
    faultModel: isScanDiagnosisKpi(kpi.id) ? "SA + TD + Cell-Aware" : undefined,
    compressionRatio: isScanDiagnosisKpi(kpi.id) ? "42.8:1" : undefined,
    suspectedPhysicalRegion: isScanDiagnosisKpi(kpi.id) ? "M3-IO / Metal M4" : undefined,
  };
}

const EXEC_REC_ACTIONS = [
  "Retry Parsing",
  "Re-run ATPG",
  "Repair Metadata",
  "Remove Redundant Patterns",
  "Optimize Scan Chains",
  "Regenerate STIL",
  "Regenerate WGL",
];

const PATTERN_REC_ACTIONS = [
  "Remove Redundant Patterns",
  "Regenerate STIL",
  "Regenerate WGL",
  "Retry Parsing",
  "Re-run Clustering",
  "Re-embed Patterns",
  "Repair Metadata",
  "Export Quality Report",
];

const FAILURE_REC_ACTIONS = [
  "Retry Test",
  "Re-run ATPG",
  "Repair Pattern",
  "Repair Scan Chain",
  "Optimize Test Program",
  "Isolate Failing Die",
  "Recalibrate Tester",
];

const DIAGNOSIS_REC_ACTIONS = [
  "Repair Scan Chain",
  "Re-run ATPG",
  "Reduce Compression",
  "Regenerate Pattern",
  "Repair Clock Domain",
  "Repair Shift Timing",
  "Isolate Failing Cell",
];

function buildRecommendations(kpiId: string, seed: number): KpiRecommendation[] {
  const actions = isScanDiagnosisKpi(kpiId)
    ? DIAGNOSIS_REC_ACTIONS
    : isFailureAnalysisKpi(kpiId)
      ? FAILURE_REC_ACTIONS
      : isPatternAnalysisKpi(kpiId)
        ? PATTERN_REC_ACTIONS
        : EXEC_REC_ACTIONS;
  return actions.slice(0, 5).map((action, i) => ({
    id: `rec-${i}`,
    action,
    priority: (["P0", "P1", "P2", "P3"] as const)[Math.min(i, 3)],
    estimatedImprovement: `+${(rnd(seed, 60 + i) * 2 + 0.5).toFixed(1)}%`,
    runtimeSaving: `-${Math.round(rnd(seed, 70 + i) * 12 + 3)}%`,
    costSaving: `$${Math.round(rnd(seed, 80 + i) * 18000 + 4000).toLocaleString()}`,
    confidence: Math.round(72 + rnd(seed, 90 + i) * 24),
  }));
}

function resolveBreakdownDimensions(kpiId: string): readonly string[] {
  if (isFailureAnalysisKpi(kpiId)) return FAILURE_BREAKDOWN_DIMENSIONS;
  if (isScanDiagnosisKpi(kpiId)) return DIAGNOSIS_BREAKDOWN_DIMENSIONS;
  if (isPatternAgentKpi(kpiId)) return RECOMMENDATION_BREAKDOWN_DIMENSIONS;
  if (isTestOptAgentKpi(kpiId)) return TEST_OPT_BREAKDOWN_DIMENSIONS;
  if (isScanDebugAgentKpi(kpiId)) return SCAN_DEBUG_BREAKDOWN_DIMENSIONS;
  const profile = getKpiProfile(kpiId);
  if (profile.breakdownDimensions.length > 0) return profile.breakdownDimensions;
  return KPI_BREAKDOWN_DIMENSIONS;
}

function buildBreakdowns(kpi: DrillDownKPI, seed: number, dimensions: readonly string[]): Record<string, KpiBreakdownSlice[]> {
  const labels: Record<string, string[]> = {
    fab: ["FAB-12", "FAB-08", "FAB-15"],
    tester: ["T-104", "T-108", "T-112"],
    product: ["X7-ASIC", "Y9-SoC", "Z3-IO"],
    lot: ["LOT-A2847", "LOT-B1923", "LOT-C4412"],
    wafer: ["W-042", "W-051", "W-038"],
    module: ["M1-Core", "M3-IO", "M5-Cache"],
    pattern: ["PAT-4821", "PAT-7892", "PAT-3156"],
    scanChain: ["SC-004821", "SC-007892", "SC-003156"],
    vector: ["VEC-128442", "VEC-99201", "VEC-77410"],
    die: ["D-042", "D-18", "D-22"],
    failureBin: ["BIN-7 Bridge", "BIN-12 Open", "BIN-3 Delay"],
    scanCell: ["SC_14-142", "SC_08-88", "SC_21-201"],
    flop: ["FF_M3_142", "FF_M3_088", "FF_IO_201"],
    patternGroup: ["Cluster-A", "Cluster-B", "Cluster-C"],
    faultModel: ["Stuck-at", "Transition", "Bridging"],
    coverage: ["98.1%", "98.8%", "99.3%"],
    compression: ["42:1", "38:1", "35:1"],
    runtime: ["4.2h", "3.8h", "3.4h"],
    site: ["Site-1", "Site-4", "Site-8", "Site-12"],
    package: ["FCBGA-2560", "BGA-1440", "QFN-128"],
    device: ["X7-A1", "X7-B2", "Y9-C1"],
    testFlow: ["FT-Standard", "FT-Adaptive", "QA-Screen"],
    testProgram: ["X7_PROD_V3.2", "X7_ENG_V2.1", "Y9_PROD_V1.4"],
    clockDomain: ["CLK_M3_FAST", "CLK_IO_SLOW", "CLK_CORE"],
    powerDomain: ["PD_CORE", "PD_IO", "PD_ANALOG"],
  };
  const base = parseNum(kpi.value) || 100;
  return Object.fromEntries(
    dimensions.map((dim) => [
      dim,
      (labels[dim] ?? ["A", "B", "C"]).map((label, i) => ({
        dimension: dim,
        label,
        value: Math.round(base * (0.2 + rnd(seed, i * 7) * 0.25)),
        share: Math.round(15 + rnd(seed, i * 11) * 25),
        trend: Math.round((rnd(seed, i * 13) - 0.5) * 10 * 10) / 10,
      })),
    ])
  );
}

function buildTimeline(kpiId: string): KpiTimelineEvent[] {
  if (isScanDebugAgentKpi(kpiId)) {
    return [
      { id: "tl-1", type: "ai-analysis", label: "Recommendation Generated", timestamp: "08:45", status: "complete" },
      { id: "tl-2", type: "validation", label: "Engineer Review", timestamp: "09:15", status: "running" },
      { id: "tl-3", type: "recommendation", label: "Approval", timestamp: "09:45", status: "pending" },
      { id: "tl-4", type: "parsing", label: "Pattern Update", timestamp: "10:15", status: "pending" },
      { id: "tl-5", type: "validation", label: "Validation", timestamp: "10:45", status: "pending" },
      { id: "tl-6", type: "execution", label: "Regression", timestamp: "11:15", status: "pending" },
      { id: "tl-7", type: "report", label: "Production", timestamp: "11:45", status: "pending" },
    ];
  }
  if (isTestOptAgentKpi(kpiId)) {
    return [
      { id: "tl-1", type: "ai-analysis", label: "Recommendation Generated", timestamp: "08:30", status: "complete" },
      { id: "tl-2", type: "validation", label: "Engineer Review", timestamp: "09:00", status: "running" },
      { id: "tl-3", type: "execution", label: "Simulation", timestamp: "09:30", status: "pending" },
      { id: "tl-4", type: "recommendation", label: "Approval", timestamp: "10:00", status: "pending" },
      { id: "tl-5", type: "validation", label: "Validation", timestamp: "10:30", status: "pending" },
      { id: "tl-6", type: "execution", label: "Production", timestamp: "11:00", status: "pending" },
      { id: "tl-7", type: "report", label: "Completed", timestamp: "11:30", status: "pending" },
    ];
  }
  if (isPatternAgentKpi(kpiId)) {
    return [
      { id: "tl-1", type: "ai-analysis", label: "Recommendation Generated", timestamp: "09:00", status: "complete" },
      { id: "tl-2", type: "validation", label: "Engineer Review", timestamp: "09:30", status: "running" },
      { id: "tl-3", type: "execution", label: "Simulation", timestamp: "10:00", status: "pending" },
      { id: "tl-4", type: "recommendation", label: "Approval", timestamp: "10:30", status: "pending" },
      { id: "tl-5", type: "parsing", label: "Pattern Update", timestamp: "11:00", status: "pending" },
      { id: "tl-6", type: "validation", label: "Regression", timestamp: "11:30", status: "pending" },
      { id: "tl-7", type: "report", label: "Production", timestamp: "12:00", status: "pending" },
    ];
  }
  if (isScanDiagnosisKpi(kpiId)) {
    return [
      { id: "tl-1", type: "upload", label: "Upload", timestamp: "07:30", status: "complete" },
      { id: "tl-2", type: "parsing", label: "Parsing", timestamp: "07:48", status: "complete" },
      { id: "tl-3", type: "diagnosis", label: "Diagnosis", timestamp: "08:12", status: "complete" },
      { id: "tl-4", type: "ai-analysis", label: "AI Analysis", timestamp: "08:28", status: "complete" },
      { id: "tl-5", type: "recommendation", label: "Root Cause", timestamp: "08:44", status: "running" },
      { id: "tl-6", type: "recommendation", label: "Recommendation", timestamp: "09:00", status: "pending" },
      { id: "tl-7", type: "report", label: "Report", timestamp: "09:15", status: "pending" },
    ];
  }
  if (isFailureAnalysisKpi(kpiId)) {
    return [
      { id: "tl-1", type: "upload", label: "Upload", timestamp: "07:45", status: "complete" },
      { id: "tl-2", type: "execution", label: "Execution", timestamp: "08:12", status: "complete" },
      { id: "tl-3", type: "failure-detection", label: "Failure Detection", timestamp: "08:28", status: "complete" },
      { id: "tl-4", type: "diagnosis", label: "Diagnosis", timestamp: "08:44", status: "complete" },
      { id: "tl-5", type: "ai-analysis", label: "AI Analysis", timestamp: "09:00", status: "running" },
      { id: "tl-6", type: "recommendation", label: "Recommendation", timestamp: "09:15", status: "pending" },
      { id: "tl-7", type: "report", label: "Report", timestamp: "09:30", status: "pending" },
      { id: "tl-8", type: "export", label: "Export", timestamp: "09:45", status: "pending" },
    ];
  }
  if (isPatternAnalysisKpi(kpiId)) {
    return [
      { id: "tl-1", type: "upload", label: "Pattern Upload", timestamp: "08:12", status: "complete" },
      { id: "tl-2", type: "parsing", label: "STIL/WGL Parse", timestamp: "08:18", status: "complete" },
      { id: "tl-3", type: "validation", label: "Integrity Check", timestamp: "08:32", status: "complete" },
      { id: "tl-4", type: "embedding", label: "Embedding Gen", timestamp: "08:45", status: "complete" },
      { id: "tl-5", type: "ai-analysis", label: "Cluster Analysis", timestamp: "09:00", status: "running" },
      { id: "tl-6", type: "recommendation", label: "Redundancy Review", timestamp: "09:15", status: "pending" },
      { id: "tl-7", type: "report", label: "Quality Report", timestamp: "09:30", status: "pending" },
      { id: "tl-8", type: "export", label: "Pattern Export", timestamp: "09:45", status: "pending" },
    ];
  }
  return [
    { id: "tl-1", type: "upload", label: "Upload", timestamp: "08:12", status: "complete" },
    { id: "tl-2", type: "parsing", label: "Parsing", timestamp: "08:18", status: "complete" },
    { id: "tl-3", type: "validation", label: "Validation", timestamp: "08:32", status: "complete" },
    { id: "tl-4", type: "embedding", label: "Embedding", timestamp: "08:45", status: "running" },
    { id: "tl-5", type: "ai-analysis", label: "AI Analysis", timestamp: "09:00", status: "pending" },
    { id: "tl-6", type: "recommendation", label: "Recommendation", timestamp: "09:15", status: "pending" },
    { id: "tl-7", type: "report", label: "Report Generation", timestamp: "09:30", status: "pending" },
    { id: "tl-8", type: "export", label: "Export", timestamp: "09:45", status: "pending" },
  ];
}

function buildTable(kpi: DrillDownKPI, filters: KpiDrillDownFilters, seed: number) {
  const patternMode = isPatternAnalysisKpi(kpi.id);
  const failureMode = isFailureAnalysisKpi(kpi.id);
  const diagnosisMode = isScanDiagnosisKpi(kpi.id);
  const recommendationMode = isPatternAgentKpi(kpi.id);
  const testOptMode = isTestOptAgentKpi(kpi.id);
  const scanDebugMode = isScanDebugAgentKpi(kpi.id);
  const columns = scanDebugMode
    ? [
        { key: "patternId", label: "Pattern ID", frozen: true, defaultVisible: true },
        { key: "scanChainId", label: "Scan Chain ID", defaultVisible: true },
        { key: "scanCell", label: "Scan Cell", defaultVisible: true },
        { key: "vectorId", label: "Vector ID", defaultVisible: true },
        { key: "clockDomain", label: "Clock Domain", defaultVisible: true },
        { key: "faultModel", label: "Fault Model", defaultVisible: true },
        { key: "coverage", label: "Coverage", defaultVisible: true },
        { key: "power", label: "Power", defaultVisible: true },
        { key: "runtime", label: "Runtime", defaultVisible: true },
        { key: "recScore", label: "Rec. Score", defaultVisible: true },
        { key: "confidence", label: "AI Confidence", defaultVisible: true },
        { key: "decision", label: "Engineer Approval", defaultVisible: true },
      ]
    : testOptMode
    ? [
        { key: "recId", label: "Recommendation ID", frozen: true, defaultVisible: true },
        { key: "product", label: "Product", defaultVisible: true },
        { key: "lot", label: "Lot", defaultVisible: true },
        { key: "wafer", label: "Wafer", defaultVisible: true },
        { key: "tester", label: "Tester", defaultVisible: true },
        { key: "programVersion", label: "Program Version", defaultVisible: true },
        { key: "yield", label: "Yield", defaultVisible: true },
        { key: "runtime", label: "Runtime", defaultVisible: true },
        { key: "cost", label: "Cost", defaultVisible: true },
        { key: "riskScore", label: "Risk Score", defaultVisible: true },
        { key: "roi", label: "ROI", defaultVisible: true },
        { key: "recScore", label: "Rec. Score", defaultVisible: true },
        { key: "decision", label: "Engineer Decision", defaultVisible: true },
      ]
    : recommendationMode
    ? [
        { key: "patternId", label: "Pattern ID", frozen: true, defaultVisible: true },
        { key: "patternName", label: "Pattern Name", defaultVisible: true },
        { key: "patternGroup", label: "Pattern Group", defaultVisible: true },
        { key: "faultModel", label: "Fault Model", defaultVisible: true },
        { key: "coverage", label: "Coverage", defaultVisible: true },
        { key: "runtime", label: "Runtime", defaultVisible: true },
        { key: "power", label: "Power", defaultVisible: true },
        { key: "compression", label: "Compression", defaultVisible: true },
        { key: "recScore", label: "Rec. Score", defaultVisible: true },
        { key: "decision", label: "Engineer Decision", defaultVisible: true },
      ]
    : diagnosisMode
    ? [
        { key: "chainId", label: "Chain ID", frozen: true, defaultVisible: true },
        { key: "pattern", label: "Pattern", defaultVisible: true },
        { key: "vector", label: "Vector", defaultVisible: true },
        { key: "flop", label: "Flop", defaultVisible: true },
        { key: "cell", label: "Cell", defaultVisible: true },
        { key: "cycle", label: "Cycle", defaultVisible: true },
        { key: "clock", label: "Clock", defaultVisible: true },
        { key: "failCount", label: "Fail Count", defaultVisible: true },
        { key: "diagnosis", label: "Diagnosis", defaultVisible: true },
      ]
    : failureMode
    ? [
        { key: "entityId", label: "Failure ID", frozen: true, defaultVisible: true },
        { key: "entityType", label: "Type", defaultVisible: true },
        { key: "patternId", label: "Pattern", defaultVisible: true },
        { key: "lot", label: "Lot", defaultVisible: true },
        { key: "wafer", label: "Wafer", defaultVisible: true },
        { key: "faultCategory", label: "Fault Category", defaultVisible: true },
        { key: "confidence", label: "Confidence", defaultVisible: true },
        { key: "severity", label: "Severity", defaultVisible: true },
      ]
    : [
        { key: "entityId", label: "Entity ID", frozen: true, defaultVisible: true },
        { key: "entityType", label: "Type", defaultVisible: true },
        { key: "metric", label: "Metric", defaultVisible: true },
        { key: "value", label: "Value", defaultVisible: true },
        { key: "delta", label: "Delta", defaultVisible: true },
        { key: "tester", label: "Tester", defaultVisible: true },
        { key: "lot", label: "Lot", defaultVisible: false },
        { key: "severity", label: "Severity", defaultVisible: true },
      ];
  const entityIds = failureMode
    ? ["F-20481", "F-20480", "F-20479", "F-20478", "F-20477"]
    : patternMode
      ? ["PAT-8821", "PAT-7742", "VEC-128442", "CLUSTER-88", "FILE-042"]
      : ["SC-004821", "PAT-8821", "LOT-4421"];
  const entityTypes = failureMode
    ? ["Failure", "Failure", "Failure", "Failure", "Failure"]
    : patternMode
      ? ["Pattern", "Vector", "Cluster", "File", "Report"]
      : ["Chain", "Pattern", "Lot"];
  const rows = Array.from({ length: 32 }, (_, i) => {
    if (scanDebugMode) {
      return {
        id: `row-${i}`,
        patternId: ["PAT-4821", "PAT-7892", "PAT-3156"][i % 3],
        scanChainId: ["SC_14", "SC_08", "SC_21"][i % 3],
        scanCell: ["SC_14-142", "SC_08-88", "SC_21-201"][i % 3],
        vectorId: ["VEC-128442", "VEC-99201", "VEC-77410"][i % 3],
        clockDomain: ["CLK_M3_FAST", "CLK_IO_SLOW", "CLK_M3_FAST"][i % 3],
        faultModel: ["Stuck-at", "Transition", "Bridging"][i % 3],
        coverage: `${(96 + rnd(seed, i) * 3).toFixed(1)}%`,
        power: `${Math.round(55 + rnd(seed, i + 1) * 35)}W`,
        runtime: `${(2.8 + rnd(seed, i + 2) * 1.8).toFixed(1)}h`,
        recScore: `${Math.round(82 + rnd(seed, i + 3) * 16)}`,
        confidence: `${Math.round(84 + rnd(seed, i + 4) * 14)}%`,
        decision: ["Pending", "Approved", "In Review"][i % 3],
      } satisfies KpiTableRow;
    }
    if (testOptMode) {
      return {
        id: `row-${i}`,
        recId: `OPT-REC-${1040 + i}`,
        product: ["X7-ASIC", "Y9-SoC", "Z3-IO"][i % 3],
        lot: ["LOT-A2847", "LOT-B1923", "LOT-C4412"][i % 3],
        wafer: ["W-042", "W-038", "W-051"][i % 3],
        tester: ["T-104", "T-108", "T-112"][i % 3],
        programVersion: ["X7_PROD_V3.2", "X7_ENG_V2.1", "Y9_PROD_V1.4"][i % 3],
        yield: `${(86 + rnd(seed, i) * 4).toFixed(1)}%`,
        runtime: `${(42 + rnd(seed, i + 1) * 18).toFixed(0)}s`,
        cost: `$${(0.32 + rnd(seed, i + 2) * 0.12).toFixed(2)}`,
        riskScore: (0.55 + rnd(seed, i + 3) * 0.35).toFixed(2),
        roi: `${(2.8 + rnd(seed, i + 4) * 2.2).toFixed(1)}x`,
        recScore: `${Math.round(80 + rnd(seed, i + 5) * 18)}`,
        decision: ["Pending", "Approved", "In Review"][i % 3],
      } satisfies KpiTableRow;
    }
    if (recommendationMode) {
      return {
        id: `row-${i}`,
        patternId: ["PAT-9103", "PAT-4821", "PAT-NEW-018"][i % 3],
        patternName: ["Legacy SA", "Transition Block", "Bridge ATPG"][i % 3],
        patternGroup: ["Cluster-A", "Cluster-B", "Cluster-C"][i % 3],
        faultModel: ["Stuck-at", "Transition", "Bridging"][i % 3],
        coverage: `${(97 + rnd(seed, i) * 2.5).toFixed(1)}%`,
        runtime: `${(3 + rnd(seed, i + 1) * 2).toFixed(1)}h`,
        power: `${Math.round(60 + rnd(seed, i + 2) * 30)}W`,
        compression: `${Math.round(35 + rnd(seed, i + 3) * 10)}:1`,
        recScore: `${Math.round(82 + rnd(seed, i + 4) * 16)}`,
        decision: ["Pending", "Approved", "In Review"][i % 3],
      } satisfies KpiTableRow;
    }
    if (diagnosisMode) {
      return {
        id: `row-${i}`,
        chainId: ["SC_14", "SC_08", "SC_21"][i % 3],
        pattern: ["PAT-4821", "PAT-3156", "PAT-7892"][i % 3],
        vector: ["VEC-128442", "VEC-99201", "VEC-77410"][i % 3],
        flop: ["FF_M3_142", "FF_M3_088", "FF_IO_201"][i % 3],
        cell: ["SC_14-142", "SC_08-88", "SC_21-201"][i % 3],
        cycle: `${847 + (i % 12)}`,
        clock: ["CLK_M3_FAST", "CLK_IO_SLOW", "CLK_M3_FAST"][i % 3],
        failCount: Math.round(4 + rnd(seed, i) * 28),
        diagnosis: ["Chain break", "Shift fault", "Capture edge"][i % 3],
      } satisfies KpiTableRow;
    }
    if (failureMode) {
      return {
        id: `row-${i}`,
        entityId: entityIds[i % entityIds.length],
        entityType: "Failure",
        patternId: ["PAT-4821", "PAT-3156", "PAT-7892"][i % 3],
        lot: ["LOT-A2847", "LOT-B1923", "LOT-C4412"][i % 3],
        wafer: ["W-042", "W-038", "W-051"][i % 3],
        faultCategory: ["Stuck-at", "Transition Delay", "Bridging"][i % 3],
        confidence: `${Math.round(82 + rnd(seed, i) * 14)}%`,
        severity: ["P0", "P1", "P2", "P3"][i % 4],
      } satisfies KpiTableRow;
    }
    return {
      id: `row-${i}`,
      entityId: entityIds[i % entityIds.length],
      entityType: entityTypes[i % entityTypes.length],
      metric: kpi.title,
      value: kpi.value,
      delta: `${rnd(seed, i) > 0.5 ? "+" : "-"}${(rnd(seed, i + 100) * 5).toFixed(1)}%`,
      tester: filters.tester,
      lot: filters.lot,
      severity: ["P0", "P1", "P2", "P3"][i % 4],
    } satisfies KpiTableRow;
  });
  return { columns, rows: rows as unknown as KpiTableRow[] };
}

const REC_CATEGORY: Record<string, string> = {
  redundant: "Redundancy Removal",
  removal: "Pattern Removal",
  "removal-conf": "Removal Confidence",
  reorder: "Sequence Optimization",
  atpg: "ATPG Addition",
  "fault-models": "Fault Model Targeting",
  "low-power": "Low-Power Optimization",
  "power-saving": "Power Reduction",
  "coverage-delta": "Coverage Improvement",
  total: "Portfolio Optimization",
};

const TEST_OPT_CATEGORY: Record<string, string> = {
  "adaptive-recs": "Adaptive Testing",
  "test-time-red": "Test Time Reduction",
  "flow-variants": "Flow Variant Optimization",
  "stop-recs": "Test Stop Optimization",
  "escapes-prevented": "Escape Prevention",
  "active-stop-rules": "Stop Rule Management",
  "high-risk-devices": "Risk-Based Testing",
  "risk-recs": "Risk Mitigation",
  "avg-risk-score": "Risk Score Analysis",
  "current-yield": "Yield Monitoring",
  "yield-recs": "Yield Improvement",
  "projected-yield": "Yield Projection",
  "est-cost-saving": "Cost Reduction",
  "cost-recs": "Cost Optimization",
  "cost-per-device": "Unit Cost Analysis",
  "active-sites": "Multi-Site Utilization",
  "site-recs": "Site Optimization",
  "site-correlation": "Site Correlation",
  "total-opt-recs": "Portfolio Optimization",
};

const SCAN_DEBUG_CATEGORY: Record<string, string> = {
  "broken-chains": "Scan Chain Debug",
  "debug-recs": "Debug Recommendation",
  "avg-confidence": "AI Confidence",
  "constraint-violations": "ATPG Constraint Review",
  "review-recs": "Constraint Optimization",
  "coverage-impact": "Coverage Impact",
  "timing-violations": "Timing Debug",
  "timing-debug-recs": "Timing Optimization",
  "worst-slack": "Critical Timing Path",
  "power-violations": "Power Integrity",
  "power-debug-recs": "Power Optimization",
  "peak-switching": "Switching Activity",
  "defect-suspects": "Physical Defect Investigation",
  "investigation-recs": "Failure Analysis",
  "defect-localization": "Defect Localization",
};

function buildAiDecision(kpi: DrillDownKPI, seed: number): KpiAiDecisionOverview {
  const risk = riskFromChange(kpi.change, kpi.positiveIsGood ?? true);
  return {
    category: REC_CATEGORY[kpi.id] ?? "Pattern Optimization",
    reason: `AI detected ${kpi.value} ${kpi.title.toLowerCase()} opportunity based on embedding similarity and fault overlap analysis.`,
    optimizationGoal: kpi.id === "coverage-delta" ? "Maximize fault coverage with minimal pattern count" : "Reduce test time while preserving coverage",
    historicalSuccessRate: `${Math.round(84 + rnd(seed, 40) * 12)}%`,
    similarCases: Math.round(12 + rnd(seed, 41) * 28),
    engineeringBenefit: kpi.id === "power-saving" ? "-21.6% tester power" : "-12.4% runtime · +1.2% coverage",
    businessBenefit: `$${Math.round(rnd(seed, 42) * 52000 + 18000).toLocaleString()} projected savings`,
    confidence: Math.round(88 + rnd(seed, 43) * 10),
    implementationDifficulty: rnd(seed, 44) > 0.6 ? "Moderate" : "Low",
    riskLevel: risk,
  };
}

function buildAiExplanation(kpi: DrillDownKPI, seed: number): KpiAiExplanation {
  return {
    recommendationReason: `Patterns in cluster share >94% functional overlap with PAT-7892 — safe to ${kpi.id === "removal" ? "remove" : "optimize"} without coverage regression.`,
    featureImportance: [
      { feature: "Pattern Similarity", weight: Math.round(88 + rnd(seed, 50) * 8) },
      { feature: "Fault Overlap", weight: Math.round(72 + rnd(seed, 51) * 18) },
      { feature: "Runtime Weight", weight: Math.round(65 + rnd(seed, 52) * 20) },
      { feature: "Historical Success", weight: Math.round(78 + rnd(seed, 53) * 15) },
    ],
    similarCases: ["PAT-REC-042", "LOT-4418", "Release R3.1"],
    alternative: "Merge with PAT-7892 cluster instead of full removal",
    riskAnalysis: rnd(seed, 54) > 0.7 ? "Low risk — coverage delta within 0.1% tolerance" : "Medium risk — review transition patterns",
    expectedOutcome: "+1.2% coverage · -12.4% runtime · -21.6% power",
    confidence: Math.round(88 + rnd(seed, 55) * 10),
  };
}

function buildExpectedImpactMetrics(kpiId: string, seed: number): KpiExpectedImpactCard[] {
  return [
    { label: "Coverage Improvement", value: "+1.2%", delta: "98.1% → 99.3%", variant: "success" },
    { label: "Pattern Count Reduction", value: "-28", delta: "342 → 314 patterns", variant: "success" },
    { label: "Runtime Reduction", value: "-12.4%", delta: "4.2h → 3.7h", variant: "success" },
    { label: "Power Saving", value: "21.6%", delta: kpiId === "power-saving" ? "Primary KPI" : "Projected", variant: "success" },
    { label: "Memory Saving", value: "-18%", delta: "Vector store optimized", variant: "info" },
    { label: "ATE Cost Saving", value: `$${Math.round(rnd(seed, 56) * 48000 + 12000).toLocaleString()}`, delta: "Per lot estimate", variant: "success" },
    { label: "Execution Time", value: "-38 min", delta: "Per wafer", variant: "success" },
    { label: "Yield Improvement", value: "+0.4%", delta: "Escapes prevented", variant: "success" },
  ];
}

function buildTestOptAiDecision(kpi: DrillDownKPI, seed: number): KpiAiDecisionOverview {
  const risk = riskFromChange(kpi.change, kpi.positiveIsGood ?? true);
  return {
    category: TEST_OPT_CATEGORY[kpi.id] ?? "Test Optimization",
    reason: `AI identified ${kpi.value} ${kpi.title.toLowerCase()} opportunity from production history, yield analytics, and ATE utilization patterns.`,
    optimizationGoal:
      kpi.id.includes("yield") || kpi.id === "current-yield"
        ? "Maximize production yield with minimal test time increase"
        : kpi.id.includes("cost")
          ? "Reduce cost per device while maintaining quality"
          : "Optimize test time and throughput without yield regression",
    historicalSuccessRate: `${Math.round(86 + rnd(seed, 40) * 10)}%`,
    similarCases: Math.round(18 + rnd(seed, 41) * 42),
    engineeringBenefit: kpi.id === "test-time-red" ? "-18% test time · +8% throughput" : "+3.1% yield · -12% retest rate",
    businessBenefit: `$${Math.round(rnd(seed, 42) * 62000 + 24000).toLocaleString()} projected annual savings`,
    confidence: Math.round(86 + rnd(seed, 43) * 12),
    implementationDifficulty: rnd(seed, 44) > 0.55 ? "Moderate" : "Low",
    riskLevel: risk,
  };
}

function buildTestOptAiExplanation(kpi: DrillDownKPI, seed: number): KpiAiExplanation {
  return {
    recommendationReason: `Production data shows ${kpi.title.toLowerCase()} can improve by applying adaptive test flow variant FT-Adaptive with optimized stop rules on LOT-A2847.`,
    featureImportance: [
      { feature: "Historical Yield Trend", weight: Math.round(82 + rnd(seed, 50) * 12) },
      { feature: "Test Time Distribution", weight: Math.round(74 + rnd(seed, 51) * 16) },
      { feature: "Site Utilization", weight: Math.round(68 + rnd(seed, 52) * 20) },
      { feature: "Escape Rate History", weight: Math.round(71 + rnd(seed, 53) * 18) },
      { feature: "Cost per Device", weight: Math.round(79 + rnd(seed, 54) * 14) },
    ],
    similarCases: ["LOT-4418 Adaptive", "Release R3.1 Stop Rules", "Site-4 Load Balance"],
    alternative: "Apply soft-stop rules only on high-risk bins before full flow change",
    riskAnalysis: rnd(seed, 55) > 0.65 ? "Low risk — yield delta within ±0.2% tolerance" : "Medium risk — validate on engineering lot first",
    expectedOutcome: "+3.1% yield · -18% test time · $48K/lot savings · 4.2x ROI",
    confidence: Math.round(86 + rnd(seed, 56) * 12),
  };
}

function buildBusinessImpactMetrics(kpiId: string, seed: number): KpiExpectedImpactCard[] {
  void kpiId;
  return [
    { label: "Yield Gain", value: "+3.1%", delta: "87.4% → 90.5%", variant: "success" },
    { label: "Cost Reduction", value: "$48K", delta: "Per lot · $576K annual", variant: "success" },
    { label: "Runtime Reduction", value: "-18%", delta: "52s → 43s avg/device", variant: "success" },
    { label: "Power Saving", value: "14.2%", delta: "Tester energy optimized", variant: "success" },
    { label: "ATE Utilization", value: "+8.4%", delta: "Throughput increase", variant: "success" },
    { label: "Throughput Increase", value: "+12%", delta: "Units per hour", variant: "success" },
    { label: "ROI", value: "4.2x", delta: "12-month payback", variant: "success" },
    { label: "Production Capacity", value: "+6.8%", delta: "Additional wafers/week", variant: "info" },
  ];
}

function buildSimulationMetrics(): KpiImpactMetric[] {
  return [
    { label: "Pattern Count", before: "342", after: "314", delta: "-28 (-8.2%)" },
    { label: "Coverage", before: "98.1%", after: "99.3%", delta: "+1.2%" },
    { label: "Runtime", before: "4.2h", after: "3.7h", delta: "-12.4%" },
    { label: "Power", before: "100%", after: "78.4%", delta: "-21.6%" },
    { label: "Memory", before: "2.4 GB", after: "1.97 GB", delta: "-18%" },
    { label: "Cost", before: "$0.45/die", after: "$0.38/die", delta: "-15.6%" },
    { label: "Execution Time", before: "5h 12m", after: "4h 34m", delta: "-38 min" },
  ];
}

function buildTestOptSimulationMetrics(): KpiImpactMetric[] {
  return [
    { label: "Yield", before: "87.4%", after: "90.5%", delta: "+3.1%" },
    { label: "Coverage", before: "98.1%", after: "98.6%", delta: "+0.5%" },
    { label: "Runtime", before: "52s/device", after: "43s/device", delta: "-18%" },
    { label: "Power", before: "100%", after: "85.8%", delta: "-14.2%" },
    { label: "Cost", before: "$0.45/die", after: "$0.38/die", delta: "-15.6%" },
    { label: "Throughput", before: "420 UPH", after: "470 UPH", delta: "+12%" },
    { label: "ROI", before: "1.0x", after: "4.2x", delta: "+320%" },
  ];
}

function buildApprovalActions(): KpiApprovalAction[] {
  return [
    { id: "approve", label: "Approve Recommendation", description: "Apply optimization to test program", impactHint: "+1.2% coverage · -12.4% runtime", variant: "primary" },
    { id: "reject", label: "Reject Recommendation", description: "Decline with engineer comment", impactHint: "No change applied", variant: "danger" },
    { id: "simulate", label: "Run Simulation", description: "Preview before/after impact", impactHint: "Validates coverage delta", variant: "outline" },
    { id: "report", label: "Generate Engineering Report", description: "Export ATPG patch + test plan", impactHint: "PDF · Excel · STIL patch", variant: "outline" },
    { id: "assign", label: "Assign Engineer", description: "Route for DFT review", impactHint: "SLA 4h review window", variant: "outline" },
    { id: "patch", label: "Generate ATPG Patch", description: "Create Tessent-compatible patch", impactHint: "28 patterns affected", variant: "outline" },
  ];
}

function buildTestOptApprovalActions(): KpiApprovalAction[] {
  return [
    { id: "approve", label: "Approve Recommendation", description: "Apply optimization to production test flow", impactHint: "+3.1% yield · -18% test time · $48K savings", variant: "primary" },
    { id: "reject", label: "Reject Recommendation", description: "Decline with engineer comment", impactHint: "No production change", variant: "danger" },
    { id: "modify", label: "Modify Parameters", description: "Adjust thresholds before deployment", impactHint: "Custom risk/yield tradeoff", variant: "outline" },
    { id: "simulate", label: "Run Simulation", description: "Preview current vs optimized state", impactHint: "Yield · cost · runtime projection", variant: "outline" },
    { id: "program", label: "Generate Test Program", description: "Export optimized test program", impactHint: "SmarTest · IGXL compatible", variant: "outline" },
    { id: "report", label: "Generate Report", description: "Engineering + business impact report", impactHint: "PDF · Excel export", variant: "outline" },
    { id: "assign", label: "Assign Engineer", description: "Route for test engineering review", impactHint: "SLA 6h review window", variant: "outline" },
    { id: "change", label: "Create Change Request", description: "Open production change ticket", impactHint: "Jira · SAP integration", variant: "outline" },
  ];
}

function buildScanDebugAiDecision(kpi: DrillDownKPI, seed: number): KpiAiDecisionOverview {
  const risk = riskFromChange(kpi.change, kpi.positiveIsGood ?? true);
  return {
    category: SCAN_DEBUG_CATEGORY[kpi.id] ?? "Scan Debug",
    reason: `AI identified ${kpi.value} ${kpi.title.toLowerCase()} from failure logs, scan diagnosis, and ATPG constraint analysis on LOT-A2847.`,
    optimizationGoal:
      kpi.id.includes("timing") || kpi.id === "worst-slack"
        ? "Resolve timing violations without coverage regression"
        : kpi.id.includes("power") || kpi.id === "peak-switching"
          ? "Reduce power violations while maintaining scan coverage"
          : "Restore scan chain integrity and improve debug efficiency",
    historicalSuccessRate: `${Math.round(82 + rnd(seed, 40) * 14)}%`,
    similarCases: Math.round(10 + rnd(seed, 41) * 24),
    engineeringBenefit: kpi.id === "coverage-impact" ? "+1.8% coverage · -8.4% runtime" : "Chain repair · -12% debug cycle time",
    businessBenefit: `$${Math.round(rnd(seed, 42) * 28000 + 8000).toLocaleString()} estimated cost avoidance`,
    confidence: Math.round(84 + rnd(seed, 43) * 12),
    implementationDifficulty: rnd(seed, 44) > 0.5 ? "Moderate" : "Low",
    riskLevel: risk,
  };
}

function buildScanDebugAiExplanation(kpi: DrillDownKPI, seed: number): KpiAiExplanation {
  return {
    recommendationReason: `Root cause analysis links ${kpi.title.toLowerCase()} to SC_14 chain break at flop FF_M3_142 — AI recommends isolation and re-stitch before next production lot.`,
    featureImportance: [
      { feature: "Chain Topology", weight: Math.round(86 + rnd(seed, 50) * 10) },
      { feature: "Failure Frequency", weight: Math.round(78 + rnd(seed, 51) * 16) },
      { feature: "Pattern Overlap", weight: Math.round(71 + rnd(seed, 52) * 18) },
      { feature: "Historical Debug Success", weight: Math.round(74 + rnd(seed, 53) * 16) },
      { feature: "Coverage Impact", weight: Math.round(68 + rnd(seed, 54) * 20) },
    ],
    similarCases: ["SC_14 LOT-4418", "PAT-4821 Timing Fix", "Release R3.1 Constraint"],
    alternative: "Bypass broken segment and regenerate ATPG for affected module only",
    riskAnalysis: rnd(seed, 55) > 0.6 ? "Low risk — coverage delta within 0.2% tolerance" : "Medium risk — validate on engineering wafer first",
    expectedOutcome: "+1.8% coverage · -8.4% runtime · 7 chains restored · $22K savings",
    confidence: Math.round(84 + rnd(seed, 56) * 12),
  };
}

function buildScanDebugImpactMetrics(kpiId: string, seed: number): KpiExpectedImpactCard[] {
  void kpiId;
  void seed;
  return [
    { label: "Coverage Improvement", value: "+1.8%", delta: "97.2% → 99.0%", variant: "success" },
    { label: "Yield Improvement", value: "+0.6%", delta: "Escapes prevented", variant: "success" },
    { label: "Power Saving", value: "12.6%", delta: "Switching optimized", variant: "success" },
    { label: "Runtime Reduction", value: "-8.4%", delta: "Debug cycle shortened", variant: "success" },
    { label: "Memory Saving", value: "-14%", delta: "Vector store reduced", variant: "info" },
    { label: "ATE Cost Saving", value: "$22K", delta: "Per lot estimate", variant: "success" },
    { label: "Pattern Reduction", value: "-6", delta: "Redundant debug patterns", variant: "success" },
  ];
}

function buildScanDebugApprovalActions(): KpiApprovalAction[] {
  return [
    { id: "approve", label: "Approve Recommendation", description: "Apply debug fix to test program", impactHint: "+1.8% coverage · 7 chains repaired", variant: "primary" },
    { id: "reject", label: "Reject Recommendation", description: "Decline with engineer comment", impactHint: "No change applied", variant: "danger" },
    { id: "modify", label: "Modify Recommendation", description: "Adjust fix parameters", impactHint: "Custom chain/pattern scope", variant: "outline" },
    { id: "assign", label: "Assign Engineer", description: "Route for DFT debug review", impactHint: "SLA 4h review window", variant: "outline" },
    { id: "jira", label: "Create Jira Ticket", description: "Open debug tracking ticket", impactHint: "Links to SC_14 trace", variant: "outline" },
    { id: "report", label: "Generate Engineering Report", description: "Export debug analysis report", impactHint: "PDF · Excel · Tessent log", variant: "outline" },
    { id: "atpg", label: "Generate ATPG Script", description: "Create Tessent-compatible script", impactHint: "Chain repair + constraint fix", variant: "outline" },
    { id: "export", label: "Export Recommendation", description: "Export recommendation package", impactHint: "STIL · WGL · JSON", variant: "outline" },
  ];
}

function buildTraceability(filters: KpiDrillDownFilters): KpiTraceabilityNode[] {
  return [
    { id: "fab", label: "Fab", value: filters.fab.toUpperCase() },
    { id: "tester", label: "Tester", value: filters.tester },
    { id: "lot", label: "Lot", value: filters.lot.toUpperCase() },
    { id: "wafer", label: "Wafer", value: filters.wafer.toUpperCase() },
    { id: "die", label: "Die", value: filters.die },
    { id: "pattern", label: "Pattern", value: filters.pattern },
    { id: "scanChain", label: "Scan Chain", value: filters.scanChain.replace("SC-", "SC_") },
    { id: "scanCell", label: "Scan Cell", value: "SC_14-142" },
    { id: "flop", label: "Flop", value: "FF_M3_142" },
    { id: "failureBit", label: "Failure Bit", value: "BIT-847" },
    { id: "diagnosis", label: "Diagnosis", value: "Chain Break" },
  ];
}

function buildTopologyGraph(): { nodes: KpiTopologyNode[]; edges: KpiTopologyEdge[] } {
  return {
    nodes: [
      { id: "SC_14", label: "SC_14", status: "broken" },
      { id: "SC_08", label: "SC_08", status: "failing-cell" },
      { id: "SC_21", label: "SC_21", status: "broken" },
      { id: "SC_04", label: "SC_04", status: "debug" },
      { id: "SC_11", label: "SC_11", status: "warning" },
      { id: "SC_07", label: "SC_07", status: "healthy" },
      { id: "SC_19", label: "SC_19", status: "failing-cell" },
      { id: "SC_03", label: "SC_03", status: "healthy" },
    ],
    edges: [
      { from: "SC_14", to: "SC_08", broken: true },
      { from: "SC_08", to: "SC_21", broken: true },
      { from: "SC_21", to: "SC_04" },
      { from: "SC_04", to: "SC_11" },
      { from: "SC_11", to: "SC_07" },
      { from: "SC_07", to: "SC_19" },
      { from: "SC_19", to: "SC_03" },
    ],
  };
}

function buildRelatedModules(kpiId: string): KpiRelatedModule[] {
  if (isScanDebugAgentKpi(kpiId)) {
    return [
      { id: "diagnosis", label: "Scan Diagnosis Agent", route: "/dashboard/scan-chain?tab=scan-diagnosis" },
      { id: "failure", label: "Failure Analysis Agent", route: "/dashboard/scan-chain?tab=failure-analysis" },
      { id: "pattern", label: "Pattern Analysis Agent", route: "/dashboard/scan-chain?tab=pattern-analysis" },
      { id: "pattern-agent", label: "Pattern Recommendation Agent", route: "/dashboard/recommendation-analysis" },
      { id: "wafer", label: "Wafer Analysis", route: "/dashboard/wafer-analysis" },
      { id: "alerts", label: "Alerts", route: "/dashboard/alerts", badge: "4" },
      { id: "reports", label: "Reports", route: "/dashboard" },
    ];
  }
  if (isTestOptAgentKpi(kpiId)) {
    return [
      { id: "cost", label: "Cost Intelligence", route: "/dashboard/cost-intelligence" },
      { id: "yield", label: "Yield Dashboard", route: "/dashboard" },
      { id: "wafer", label: "Wafer Analysis", route: "/dashboard/wafer-analysis" },
      { id: "pattern", label: "Pattern Recommendation Agent", route: "/dashboard/recommendation-analysis" },
      { id: "scan", label: "Scan Debug Agent", route: "/dashboard/recommendation-analysis" },
      { id: "alerts", label: "Alerts", route: "/dashboard/alerts", badge: "2" },
      { id: "reports", label: "Reports", route: "/dashboard" },
    ];
  }
  if (isPatternAgentKpi(kpiId)) {
    return [
      { id: "pattern", label: "Pattern Analysis Agent", route: "/dashboard/scan-chain?tab=pattern-analysis" },
      { id: "failure", label: "Failure Analysis Agent", route: "/dashboard/scan-chain?tab=failure-analysis" },
      { id: "diagnosis", label: "Scan Diagnosis Agent", route: "/dashboard/scan-chain?tab=scan-diagnosis" },
      { id: "cost", label: "Cost Intelligence", route: "/dashboard/cost-intelligence" },
      { id: "yield", label: "Yield Dashboard", route: "/dashboard" },
      { id: "alerts", label: "Alerts", route: "/dashboard/alerts", badge: "3" },
      { id: "reports", label: "Reports", route: "/dashboard" },
    ];
  }
  if (isScanDiagnosisKpi(kpiId)) {
    return [
      { id: "failure", label: "Failure Analysis Agent", route: "/dashboard/scan-chain?tab=failure-analysis" },
      { id: "pattern", label: "Pattern Analysis Agent", route: "/dashboard/scan-chain?tab=pattern-analysis" },
      { id: "wafer", label: "Wafer Analysis", route: "/dashboard/wafer-analysis" },
      { id: "recommendation", label: "Recommendation Engine", route: "/dashboard/recommendation-analysis" },
      { id: "yield", label: "Yield Dashboard", route: "/dashboard" },
      { id: "cost", label: "Cost Intelligence", route: "/dashboard/cost-intelligence" },
      { id: "alerts", label: "Alerts", route: "/dashboard/alerts", badge: "3" },
      { id: "reports", label: "Reports", route: "/dashboard" },
    ];
  }
  if (isFailureAnalysisKpi(kpiId)) {
    return [
      { id: "pattern", label: "Pattern Analysis Agent", route: "/dashboard/scan-chain?tab=pattern-analysis" },
      { id: "diagnosis", label: "Scan Diagnosis Agent", route: "/dashboard/scan-chain?tab=scan-diagnosis" },
      { id: "wafer", label: "Wafer Analysis", route: "/dashboard/wafer-analysis" },
      { id: "recommendation", label: "Recommendation Engine", route: "/dashboard/recommendation-analysis" },
      { id: "yield", label: "Yield Dashboard", route: "/dashboard" },
      { id: "cost", label: "Cost Intelligence", route: "/dashboard/cost-intelligence" },
      { id: "alerts", label: "Alerts", route: "/dashboard/alerts", badge: "3" },
      { id: "reports", label: "Reports", route: "/dashboard" },
    ];
  }
  if (isPatternAnalysisKpi(kpiId)) {
    return [
      { id: "overview", label: "Scan Chain Overview", route: "/dashboard/scan-chain?tab=overview" },
      { id: "failure", label: "Failure Analysis Agent", route: "/dashboard/scan-chain?tab=failure-analysis" },
      { id: "diagnosis", label: "Scan Diagnosis Agent", route: "/dashboard/scan-chain?tab=scan-diagnosis" },
      { id: "recommendation", label: "Pattern Recommendation Agent", route: "/dashboard/recommendation-analysis" },
      { id: "wafer", label: "Wafer Analysis", route: "/dashboard/wafer-analysis" },
      { id: "cost", label: "Cost Intelligence", route: "/dashboard/cost-intelligence" },
      { id: "yield", label: "Yield Dashboard", route: "/dashboard" },
      { id: "alerts", label: "Alerts", route: "/dashboard/alerts", badge: "3" },
      { id: "reports", label: "Reports", route: "/dashboard" },
    ];
  }
  return [
    { id: "pattern", label: "Pattern Analysis Agent", route: "/dashboard/scan-chain?tab=pattern-analysis" },
    { id: "failure", label: "Failure Analysis Agent", route: "/dashboard/scan-chain?tab=failure-analysis" },
    { id: "diagnosis", label: "Scan Diagnosis Agent", route: "/dashboard/scan-chain?tab=scan-diagnosis" },
    { id: "recommendation", label: "Recommendation Analysis", route: "/dashboard/recommendation-analysis" },
    { id: "wafer", label: "Wafer Analysis", route: "/dashboard/wafer-analysis" },
    { id: "cost", label: "Cost Intelligence", route: "/dashboard/cost-intelligence" },
    { id: "yield", label: "Yield Dashboard", route: "/dashboard" },
    { id: "alerts", label: "Alerts", route: "/dashboard/alerts", badge: "3" },
    { id: "reports", label: "Reports", route: "/dashboard" },
  ];
}

function buildSemiconductorMeta(filters: KpiDrillDownFilters, kpi: DrillDownKPI): KpiSemiconductorMeta {
  return {
    patternId: filters.pattern || "PAT-8821",
    vectorId: filters.vector || "VEC-128442",
    scanChainId: filters.scanChain || "SC-004821",
    scanCell: "SC_CELL_8821",
    flopId: "FF_M3_8821",
    compressionRatio: "42.8:1",
    atpgVersion: "Tessent 2024.1",
    tester: filters.tester,
    programVersion: "X7_PROD_V3.2",
    failBin: "BIN-7 Bridge",
    defectClass: "Bridge / Open",
    clockDomain: "CLK_M3_FAST",
    faultModel: "SA + TD + Cell-Aware",
    coverage: kpi.id === "scan-coverage" || kpi.id === "pattern-coverage-kpi" ? kpi.value : "98.4%",
    diagnosisConfidence: kpi.id === "avg-diagnosis-confidence" || kpi.id === "root-cause-confidence" || kpi.id === "sd-avg-confidence" ? kpi.value : isPatternAgentKpi(kpi.id) && kpi.id === "removal-conf" ? kpi.value : "91%",
    recommendationScore: isRecommendationAgentKpi(kpi.id) ? `${Math.round(85 + rnd(hashSeed(kpi.id), 1) * 12)}` : undefined,
    yield: isTestOptAgentKpi(kpi.id) ? "87.4%" : undefined,
    runtime: isTestOptAgentKpi(kpi.id) ? "52s/device" : isScanDebugAgentKpi(kpi.id) ? "2.8h" : undefined,
    cost: isTestOptAgentKpi(kpi.id) ? "$0.45/die" : undefined,
    riskScore: isTestOptAgentKpi(kpi.id) ? "0.74" : undefined,
    roi: isTestOptAgentKpi(kpi.id) ? "4.2x" : undefined,
    engineerApproval: isScanDebugAgentKpi(kpi.id) || isTestOptAgentKpi(kpi.id) ? "Pending Review" : undefined,
    power: isScanDebugAgentKpi(kpi.id) ? "68W" : undefined,
  };
}

export function buildKpiWorkspace(kpi: DrillDownKPI, filters: KpiDrillDownFilters): KpiWorkspaceData {
  const seed = hashSeed(`${kpi.id}-${JSON.stringify(filters)}`);
  const profile = getKpiProfile(kpi.id);
  const mod = workspaceModule(kpi.id);
  const layoutPreset = workspaceLayoutPreset(kpi.id);
  const breakdownDimensions = resolveBreakdownDimensions(kpi.id);
  const copilotSuggestions = isScanDebugAgentKpi(kpi.id)
    ? SCAN_DEBUG_COPILOT_SUGGESTIONS
    : isTestOptAgentKpi(kpi.id)
    ? TEST_OPT_COPILOT_SUGGESTIONS
    : isPatternAgentKpi(kpi.id)
    ? RECOMMENDATION_COPILOT_SUGGESTIONS
    : isScanDiagnosisKpi(kpi.id)
      ? DIAGNOSIS_COPILOT_SUGGESTIONS
      : isFailureAnalysisKpi(kpi.id)
        ? FAILURE_COPILOT_SUGGESTIONS
        : DEFAULT_COPILOT_SUGGESTIONS;
  const trendTabOptions = isScanDiagnosisKpi(kpi.id) ? DIAGNOSIS_TREND_TABS : KPI_TREND_TABS;
  void profile;

  const trendTabs: KpiTrendTab[] = ["24h", "7d", "30d", "90d", "prev-lot", "prev-release"];
  const statusVariant = (): KpiWorkspaceHeader["statusVariant"] => {
    const r = riskFromChange(kpi.change, kpi.positiveIsGood ?? true);
    if (r === "critical" || r === "high") return "danger";
    if (r === "medium") return "warning";
    return "success";
  };

  return {
    kpi,
    module: mod,
    layoutPreset,
    breakdownDimensions,
    copilotSuggestions,
    trendTabOptions,
    topologyFirst: topologyFirstKpi(kpi.id),
    traceability: buildTraceability(filters),
    topologyGraph: buildTopologyGraph(),
    header: {
      kpiId: kpi.id,
      icon: kpi.icon,
      name: kpi.title,
      currentValue: kpi.value,
      statusBadge:
        statusVariant() === "danger"
          ? "Action Required"
          : statusVariant() === "warning"
            ? "Monitor"
            : isScanDebugAgentKpi(kpi.id)
              ? "Debug Pending"
              : isTestOptAgentKpi(kpi.id)
              ? "Optimization Pending"
              : isPatternAgentKpi(kpi.id)
              ? "Pending Review"
              : isScanDiagnosisKpi(kpi.id)
                ? "Diagnosis Active"
                : isFailureAnalysisKpi(kpi.id)
                  ? "Within Target"
                  : "Nominal",
      statusVariant: statusVariant(),
      trendLabel: `${kpi.change >= 0 ? "+" : ""}${kpi.change}%`,
      trendDirection: kpi.change === 0 ? "flat" : kpi.trend === "up" ? "up" : "down",
      riskLevel: riskFromChange(kpi.change, kpi.positiveIsGood ?? true),
      lastUpdated: new Date().toISOString(),
      diagnosisConfidence: isScanDiagnosisKpi(kpi.id) ? "91%" : isRecommendationAgentKpi(kpi.id) ? `${Math.round(88 + rnd(seed, 43) * 10)}%` : undefined,
      recommendationStatus: isRecommendationAgentKpi(kpi.id) ? "Pending Review" : undefined,
      recommendationPriority: isRecommendationAgentKpi(kpi.id) ? (["P0", "P1", "P2"] as const)[Math.floor(rnd(seed, 57) * 3)] : undefined,
      recommendationVersion: isRecommendationAgentKpi(kpi.id) ? "v2.4.1" : undefined,
      aiVersion: isRecommendationAgentKpi(kpi.id) ? "Verilumen-AI v2.4.0" : undefined,
      activeFilters: {
        fab: filters.fab,
        tester: filters.tester,
        product: filters.product,
        lot: filters.lot,
        wafer: filters.wafer,
      },
    },
    executiveSummary: buildExecutiveSummary(kpi, seed),
    trendAnalytics: Object.fromEntries(trendTabs.map((t) => [t, buildTrendTab(t, kpi, seed)])) as Record<
      KpiTrendTab,
      KpiTrendAnalytics
    >,
    widgets: buildWidgetSpecs(kpi.id, seed),
    breakdowns: buildBreakdowns(kpi, seed, breakdownDimensions),
    rootCause: buildRootCause(kpi, filters, seed),
    recommendations: buildRecommendations(kpi.id, seed),
    timeline: buildTimeline(kpi.id),
    table: buildTable(kpi, filters, seed),
    relatedModules: buildRelatedModules(kpi.id),
    semiconductorMeta: buildSemiconductorMeta(filters, kpi),
    approvalActions: isPatternAgentKpi(kpi.id)
      ? buildApprovalActions()
      : isTestOptAgentKpi(kpi.id)
        ? buildTestOptApprovalActions()
        : isScanDebugAgentKpi(kpi.id)
          ? buildScanDebugApprovalActions()
          : undefined,
    aiDecision: isPatternAgentKpi(kpi.id)
      ? buildAiDecision(kpi, seed)
      : isTestOptAgentKpi(kpi.id)
        ? buildTestOptAiDecision(kpi, seed)
        : isScanDebugAgentKpi(kpi.id)
          ? buildScanDebugAiDecision(kpi, seed)
          : undefined,
    aiExplanation: isPatternAgentKpi(kpi.id)
      ? buildAiExplanation(kpi, seed)
      : isTestOptAgentKpi(kpi.id)
        ? buildTestOptAiExplanation(kpi, seed)
        : isScanDebugAgentKpi(kpi.id)
          ? buildScanDebugAiExplanation(kpi, seed)
          : undefined,
    expectedImpactMetrics: isPatternAgentKpi(kpi.id)
      ? buildExpectedImpactMetrics(kpi.id, seed)
      : isTestOptAgentKpi(kpi.id)
        ? buildBusinessImpactMetrics(kpi.id, seed)
        : isScanDebugAgentKpi(kpi.id)
          ? buildScanDebugImpactMetrics(kpi.id, seed)
          : undefined,
    simulationMetrics: isPatternAgentKpi(kpi.id)
      ? buildSimulationMetrics()
      : isTestOptAgentKpi(kpi.id)
        ? buildTestOptSimulationMetrics()
        : undefined,
    footer: {
      recordCount: 1240 + Math.floor(rnd(seed, 300) * 800),
      lastRefresh: new Date().toLocaleTimeString(),
      backendStatus: rnd(seed, 301) > 0.97 ? "degraded" : "online",
      databaseStatus: rnd(seed, 302) > 0.98 ? "slow" : "connected",
      parserVersion: "v3.2.1",
      aiModelVersion: "Verilumen-AI v2.4.0",
      latencyMs: Math.round(42 + rnd(seed, 303) * 80),
    },
  };
}

export function defaultDrillDownFilters(global?: Partial<KpiDrillDownFilters>): KpiDrillDownFilters {
  return {
    fab: global?.fab ?? "fab-12",
    site: global?.site ?? "SITE-Austin",
    tester: global?.tester ?? "T-104",
    handler: global?.handler ?? "H-2",
    product: global?.product ?? "X7-ASIC",
    package: global?.package ?? "FCBGA-2560",
    lot: global?.lot ?? "lot-4421",
    wafer: global?.wafer ?? "wafer-12",
    die: global?.die ?? "D-042",
    module: global?.module ?? "M3-IO",
    scanChain: global?.scanChain ?? "SC-004821",
    pattern: global?.pattern ?? "PAT-8821",
    vector: global?.vector ?? "VEC-128442",
    timeRange: global?.timeRange ?? "7d",
  };
}
