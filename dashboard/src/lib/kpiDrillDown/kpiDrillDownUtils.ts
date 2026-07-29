import type { FailureAnalysisKPI, PatternAnalysisKPI, ScanDiagnosisKPI, ScanKPI } from "@/types/scanChain";
import type { CenterKPI } from "@/types/recommendation";
import type { UnifiedKPI } from "@/types/kpi";
import type { DrillDownKPI, KpiWorkspaceLayoutPreset, KpiWorkspaceModule } from "@/types/kpiDrillDown";

export const PATTERN_ANALYSIS_KPI_IDS = [
  "files-ingested",
  "vectors-parsed",
  "file-integrity",
  "pattern-coverage-kpi",
  "metadata-extracted",
  "embeddings-generated",
  "pattern-clusters",
  "redundant-patterns",
  "similarity-analyses",
  "pass-fail-linked",
  "quality-reports",
] as const;

export const FAILURE_ANALYSIS_KPI_IDS = [
  "imported-files",
  "overall-failure-rate",
  "failing-patterns",
  "die-failure-rate",
  "wafer-failure-rate",
  "lot-failure-rate",
  "fault-categories",
  "root-cause-confidence",
  "recurring-failures",
] as const;

export const SCAN_DIAGNOSIS_KPI_IDS = [
  "sd-failing-chains",
  "sd-failing-cells",
  "sd-chain-breaks",
  "sd-shift-capture",
  "sd-topology-chains",
  "sd-chains-ranked",
  "sd-failure-correlations",
  "sd-top-failing-chain",
  "sd-diagnosis-reports",
  "sd-debug-locations",
  "sd-avg-confidence",
  "sd-pending-review",
] as const;

export const PATTERN_AGENT_KPI_IDS = [
  "redundant",
  "removal",
  "removal-conf",
  "reorder",
  "atpg",
  "fault-models",
  "low-power",
  "power-saving",
  "coverage-delta",
  "total",
] as const;

export const TEST_OPT_AGENT_KPI_IDS = [
  "adaptive-recs",
  "test-time-red",
  "flow-variants",
  "stop-recs",
  "escapes-prevented",
  "active-stop-rules",
  "high-risk-devices",
  "risk-recs",
  "avg-risk-score",
  "current-yield",
  "yield-recs",
  "projected-yield",
  "est-cost-saving",
  "cost-recs",
  "cost-per-device",
  "active-sites",
  "site-recs",
  "site-correlation",
  "total-opt-recs",
] as const;

export const SCAN_DEBUG_AGENT_KPI_IDS = [
  "broken-chains",
  "debug-recs",
  "avg-confidence",
  "constraint-violations",
  "review-recs",
  "coverage-impact",
  "timing-violations",
  "timing-debug-recs",
  "worst-slack",
  "power-violations",
  "power-debug-recs",
  "peak-switching",
  "defect-suspects",
  "investigation-recs",
  "defect-localization",
] as const;

export function isPatternAnalysisKpi(kpiId: string): boolean {
  return (PATTERN_ANALYSIS_KPI_IDS as readonly string[]).includes(kpiId);
}

export function isFailureAnalysisKpi(kpiId: string): boolean {
  return (FAILURE_ANALYSIS_KPI_IDS as readonly string[]).includes(kpiId);
}

export function isScanDiagnosisKpi(kpiId: string): boolean {
  return (SCAN_DIAGNOSIS_KPI_IDS as readonly string[]).includes(kpiId);
}

export function isPatternAgentKpi(kpiId: string): boolean {
  return (PATTERN_AGENT_KPI_IDS as readonly string[]).includes(kpiId);
}

export function isTestOptAgentKpi(kpiId: string): boolean {
  return (TEST_OPT_AGENT_KPI_IDS as readonly string[]).includes(kpiId);
}

export function isScanDebugAgentKpi(kpiId: string): boolean {
  return (SCAN_DEBUG_AGENT_KPI_IDS as readonly string[]).includes(kpiId);
}

export function isOptimizationAgentKpi(kpiId: string): boolean {
  return isPatternAgentKpi(kpiId) || isTestOptAgentKpi(kpiId);
}

export function isRecommendationAgentKpi(kpiId: string): boolean {
  return isPatternAgentKpi(kpiId) || isTestOptAgentKpi(kpiId) || isScanDebugAgentKpi(kpiId);
}

export function scanDebugTopologyHero(kpiId: string): boolean {
  return ["broken-chains", "debug-recs", "timing-violations", "worst-slack"].includes(kpiId);
}

export function workspaceModule(kpiId: string): KpiWorkspaceModule {
  if (isScanDebugAgentKpi(kpiId)) return "scanDebug";
  if (isTestOptAgentKpi(kpiId)) return "testOptimization";
  if (isPatternAgentKpi(kpiId)) return "recommendation";
  if (isScanDiagnosisKpi(kpiId)) return "diagnosis";
  if (isFailureAnalysisKpi(kpiId)) return "failure";
  if (isPatternAnalysisKpi(kpiId)) return "pattern";
  return "executive";
}

export function workspaceLayoutPreset(kpiId: string): KpiWorkspaceLayoutPreset {
  if (isScanDebugAgentKpi(kpiId)) return "debug";
  if (isOptimizationAgentKpi(kpiId)) return "optimization";
  if (isScanDiagnosisKpi(kpiId)) return "diagnosis";
  if (isFailureAnalysisKpi(kpiId)) return "failure";
  return "standard";
}

export function topologyFirstKpi(kpiId: string): boolean {
  return [
    "sd-failing-chains",
    "sd-failing-cells",
    "sd-chain-breaks",
    "sd-topology-chains",
    "sd-top-failing-chain",
  ].includes(kpiId);
}

export function toDrillDownKPI(
  kpi: ScanKPI | PatternAnalysisKPI | FailureAnalysisKPI | ScanDiagnosisKPI | CenterKPI | UnifiedKPI
): DrillDownKPI {
  return {
    id: kpi.id,
    title: kpi.title,
    value: kpi.value,
    subtitle: kpi.subtitle,
    change: kpi.change,
    trend: kpi.trend,
    sparkline: kpi.sparkline,
    icon: kpi.icon,
    positiveIsGood: kpi.positiveIsGood ?? true,
  };
}

export const FAILURE_COPILOT_SUGGESTIONS = [
  "Why did failures increase?",
  "Show similar lots",
  "Compare previous wafer",
  "Predict next failure",
  "Suggest optimization",
];

export const DIAGNOSIS_COPILOT_SUGGESTIONS = [
  "Why did Chain 14 fail?",
  "Compare previous lot",
  "Show similar failures",
  "Predict recurring failures",
  "Suggest ATPG improvements",
];

export const RECOMMENDATION_COPILOT_SUGGESTIONS = [
  "Why was this pattern selected?",
  "Which duplicate patterns exist?",
  "Show similar ATPG optimizations",
  "Estimate runtime reduction",
  "Estimate coverage improvement",
  "Suggest safer optimization",
];

export const TEST_OPT_COPILOT_SUGGESTIONS = [
  "Why was this optimization suggested?",
  "Estimate production savings",
  "Show similar historical optimizations",
  "Compare previous lot",
  "Predict ROI",
  "Suggest better strategy",
];

export const SCAN_DEBUG_COPILOT_SUGGESTIONS = [
  "Why was this recommendation generated?",
  "Show similar debug cases",
  "Compare previous lot",
  "Estimate runtime improvement",
  "Estimate coverage gain",
  "Suggest alternative fix",
];

export const DEFAULT_COPILOT_SUGGESTIONS = [
  "Why did coverage drop?",
  "Why did the parser fail?",
  "Compare previous lot",
  "Show similar failures",
  "Predict next failure",
  "Recommend optimization",
];
