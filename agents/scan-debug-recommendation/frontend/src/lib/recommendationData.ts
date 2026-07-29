import type {
  KpiCardModel,
  KpiSectionId,
  ScanDebugDashboardData,
  ScanDebugKpiId,
} from "@/types/kpiDrillDown";

export interface SectionProfile {
  id: KpiSectionId;
  title: string;
  eyebrow: string;
  description: string;
}

export const SECTION_PROFILES: SectionProfile[] = [
  {
    id: "scan_chain_debug",
    title: "Scan Chain Debug Recommendations",
    eyebrow: "Inspect Scan Chain",
    description:
      "Broken chains detected — inspect critical chains, locate breaks, and apply scan chain debug actions.",
  },
  {
    id: "atpg_constraint_review",
    title: "ATPG Constraint Review Recommendations",
    eyebrow: "Review ATPG Constraints",
    description:
      "Constraint and coverage issues — review ATPG masks, constraints, and pattern readiness.",
  },
  {
    id: "timing_debug",
    title: "Timing Debug Recommendations",
    eyebrow: "Review Capture Clock Timing",
    description:
      "Capture clock timing failures — review slack, clock paths, and capture margin fixes.",
  },
  {
    id: "power_related_debug",
    title: "Power-Related Debug Recommendations",
    eyebrow: "Check IR-Drop During Capture",
    description:
      "Power and IR-drop during capture — investigate peak switching and capture power violations.",
  },
  {
    id: "physical_defect_investigation",
    title: "Physical Defect Investigation Recommendations",
    eyebrow: "Investigate Physical Defect",
    description:
      "Bitmap and defect localization — prioritize PFA suspects and physical defect investigation.",
  },
];

export const KPI_ORDER: Record<KpiSectionId, ScanDebugKpiId[]> = {
  scan_chain_debug: ["broken_chains", "debug_recommendations", "avg_ai_confidence"],
  atpg_constraint_review: ["constraint_violations", "pending_review", "coverage_impact"],
  timing_debug: ["timing_violations", "timing_debug_recs", "worst_slack"],
  power_related_debug: ["power_violations", "power_debug_recs", "peak_switching"],
  physical_defect_investigation: ["defect_suspects", "investigation_recs", "defect_localization"],
};

export const KPI_VIS_MAP: Record<
  ScanDebugKpiId,
  | "topology"
  | "wafer"
  | "timing"
  | "heatmap"
  | "clock_tree"
  | "dependency"
  | "power"
  | "critical_path"
  | "priority_matrix"
  | "gauge"
  | "assignment"
  | "history"
> = {
  broken_chains: "topology",
  debug_recommendations: "priority_matrix",
  avg_ai_confidence: "gauge",
  constraint_violations: "dependency",
  pending_review: "assignment",
  coverage_impact: "heatmap",
  timing_violations: "timing",
  timing_debug_recs: "clock_tree",
  worst_slack: "critical_path",
  power_violations: "power",
  power_debug_recs: "power",
  peak_switching: "heatmap",
  defect_suspects: "wafer",
  investigation_recs: "history",
  defect_localization: "wafer",
};

const spark = (seed: number) =>
  Array.from({ length: 12 }, (_, i) => Math.max(2, Math.round(seed + Math.sin(i / 2) * seed * 0.15 + i)));

export const MOCK_KPIS: KpiCardModel[] = [
  {
    id: "broken_chains",
    section: "scan_chain_debug",
    title: "Broken Chains Detected",
    value: 18,
    target: 8,
    trendPct: 12,
    sparkline: spark(16),
    status: "breach",
    severity: "critical",
    tooltip: "Chains with breaks — inspect critical scan chains first",
  },
  {
    id: "debug_recommendations",
    section: "scan_chain_debug",
    title: "Scan Chain Debug Recommendations",
    value: 42,
    target: 30,
    trendPct: 8,
    sparkline: spark(38),
    status: "at_risk",
    severity: "high",
    tooltip: "Most critical dies recommended for Inspect Scan Chain (break + high mismatch)",
  },
  {
    id: "avg_ai_confidence",
    section: "scan_chain_debug",
    title: "Scan Chain Confidence",
    value: "87%",
    target: "90%",
    trendPct: 3,
    sparkline: spark(84),
    status: "improving",
    severity: "medium",
    tooltip: "Weighted confidence: pattern consistency × (1/ambiguity) × historical match boost",
  },
  {
    id: "constraint_violations",
    section: "atpg_constraint_review",
    title: "Constraint Violations",
    value: 11,
    target: 5,
    trendPct: -4,
    sparkline: spark(14),
    status: "at_risk",
    severity: "high",
    tooltip: "ATPG / capture constraint violations under review",
  },
  {
    id: "pending_review",
    section: "atpg_constraint_review",
    title: "Review Recommendation",
    value: 51,
    target: 6,
    trendPct: 5,
    sparkline: spark(12),
    status: "breach",
    severity: "high",
    tooltip: "Category-specific ATPG review (Reset / Scan Enable / Clock) + historical cite",
  },
  {
    id: "coverage_impact",
    section: "atpg_constraint_review",
    title: "Coverage Impact",
    value: "~6%",
    target: "<1%",
    trendPct: -2,
    sparkline: spark(20),
    status: "at_risk",
    severity: "medium",
    tooltip: "Share of failing patterns per constraint signature (estimate only)",
  },
  {
    id: "timing_violations",
    section: "timing_debug",
    title: "Timing Violations",
    value: 9,
    target: 3,
    trendPct: 6,
    sparkline: spark(10),
    status: "breach",
    severity: "critical",
    tooltip: "Capture / launch timing violations linked to failures",
  },
  {
    id: "timing_debug_recs",
    section: "timing_debug",
    title: "Timing Debug Recommendations",
    value: 7,
    target: 4,
    trendPct: 2,
    sparkline: spark(7),
    status: "at_risk",
    severity: "high",
    tooltip: "AI recommendations classified as TIMING_DEBUG",
  },
  {
    id: "worst_slack",
    section: "timing_debug",
    title: "Worst Slack",
    value: "-142ps",
    target: ">0ps",
    trendPct: -9,
    sparkline: spark(30),
    status: "breach",
    severity: "critical",
    tooltip: "Most negative path slack among failing dies",
  },
  {
    id: "power_violations",
    section: "power_related_debug",
    title: "Power Violations",
    value: 6,
    target: 2,
    trendPct: 1,
    sparkline: spark(6),
    status: "at_risk",
    severity: "high",
    tooltip: "IR-drop / peak-current violations during capture",
  },
  {
    id: "power_debug_recs",
    section: "power_related_debug",
    title: "Power Debug Recommendations",
    value: 5,
    target: 3,
    trendPct: 0,
    sparkline: spark(5),
    status: "stable",
    severity: "medium",
    tooltip: "Check IR-drop during capture — measured value, % above threshold, historical IR-fail cites",
  },
  {
    id: "peak_switching",
    section: "power_related_debug",
    title: "Peak Switching",
    value: "28mV | avg 22mV",
    target: "avg",
    trendPct: 7,
    sparkline: spark(22),
    status: "breach",
    severity: "high",
    tooltip: "MAX(IR_DROP_MV) switching-activity proxy vs run average",
  },
  {
    id: "defect_suspects",
    section: "physical_defect_investigation",
    title: "Defect Suspects",
    value: 25,
    target: 10,
    trendPct: 4,
    sparkline: spark(20),
    status: "at_risk",
    severity: "high",
    tooltip: "Top-N diagnosis nets validated by failing-pattern consistency",
  },
  {
    id: "investigation_recs",
    section: "physical_defect_investigation",
    title: "Investigation Recommendations",
    value: 8,
    target: 5,
    trendPct: 3,
    sparkline: spark(8),
    status: "at_risk",
    severity: "medium",
    tooltip: "Investigate top nets after TF/IR cross-check + historical PFA cite",
  },
  {
    id: "defect_localization",
    section: "physical_defect_investigation",
    title: "Defect Localization",
    value: "91%",
    target: "95%",
    trendPct: 2,
    sparkline: spark(88),
    status: "improving",
    severity: "low",
    tooltip: "Average localization confidence from suspects + TF/IR + FR-009 XY + PFA history",
  },
];

export function getDashboardData(): ScanDebugDashboardData {
  return {
    kpis: MOCK_KPIS,
    rootCauseDistribution: [
      { name: "Check IR-Drop During Capture", value: 979, fill: "#EF4444" },
      { name: "Review ATPG Constraints", value: 51, fill: "#38BDF8" },
      { name: "Review Capture Clock Timing", value: 47, fill: "#F59E0B" },
      { name: "Inspect Scan Chain", value: 44, fill: "#7C3AED" },
      { name: "Investigate Physical Defect", value: 25, fill: "#10B981" },
    ],
    recommendationPriority: [
      { name: "Critical", value: 55, fill: "#EF4444" },
      { name: "High", value: 95, fill: "#F59E0B" },
      { name: "Medium", value: 1035, fill: "#7C3AED" },
      { name: "Low", value: 11, fill: "#64748B" },
    ],
    recommendationTrend: Array.from({ length: 30 }, (_, i) => {
      const total = 979 + 51 + 47 + 44 + 25;
      const base = total / 30;
      const wave = 0.55 + 0.45 * (((i % 7) + 1) / 7);
      const peak = [4, 11, 18, 25].includes(i) ? 1.35 : 1;
      return {
        date: `D-${29 - i}`,
        value: Math.max(1, Math.round(base * wave * peak)),
      };
    }),
    aiConfidence: 0.87,
    approvalTrend: Array.from({ length: 12 }, (_, i) => ({
      date: `W${i + 1}`,
      value: 0,
      approved: 6 + (i % 4),
      rejected: 1 + (i % 3),
      pending: 3 + (i % 2),
    })),
    recommendations: [
      {
        id: "DBG-REC-001",
        category: "SCAN_CHAIN_DEBUG",
        categoryLabel: "Broken Chain",
        recommendation: "Inspect Scan Chain",
        scanChain: "SC-004821",
        rootCause: "Chain Breakpoint",
        actionLabel: "Inspect Scan Chain 12",
        priority: "P0",
        priorityLabel: "Critical",
        affectedScanChain: "LOT_1_Center",
        expectedImpact: "Restore chain integrity",
        expectedYieldGainPct: 1.8,
        estimatedRuntimeReductionPct: 6.2,
        confidence: 0.94,
      },
      {
        id: "DBG-REC-002",
        category: "TIMING_DEBUG",
        categoryLabel: "Timing",
        recommendation: "Review Capture Clock Timing",
        scanChain: "SC-003158",
        rootCause: "Hold Violation",
        actionLabel: "Review Capture Clock Timing",
        priority: "P1",
        priorityLabel: "High",
        affectedScanChain: "LOT_6_Near-Full",
        expectedImpact: "42 ps slack recovery",
        expectedYieldGainPct: 1.1,
        estimatedRuntimeReductionPct: 3.4,
        confidence: 0.88,
      },
      {
        id: "DBG-REC-003",
        category: "POWER_RELATED_DEBUG",
        categoryLabel: "Power",
        recommendation: "Check IR-Drop During Capture",
        scanChain: "SC-002114",
        rootCause: "IR Drop",
        actionLabel: "Check IR-Drop During Capture",
        priority: "P1",
        priorityLabel: "High",
        affectedScanChain: "LOT_1_Center",
        expectedImpact: "Stabilize capture power",
        expectedYieldGainPct: 0.9,
        estimatedRuntimeReductionPct: 2.1,
        confidence: 0.81,
      },
      {
        id: "DBG-REC-004",
        category: "ATPG_CONSTRAINT_REVIEW",
        categoryLabel: "ATPG Constraint",
        recommendation: "Review ATPG Constraints",
        scanChain: "SC-001778",
        rootCause: "Constraint Conflict",
        actionLabel: "Review ATPG Constraints",
        priority: "P2",
        priorityLabel: "Medium",
        affectedScanChain: "LOT_3_Local",
        expectedImpact: "+0.8% coverage",
        expectedYieldGainPct: 0.6,
        estimatedRuntimeReductionPct: 8.5,
        confidence: 0.79,
      },
      {
        id: "DBG-REC-005",
        category: "PHYSICAL_DEFECT_INVESTIGATION",
        categoryLabel: "Physical Defect",
        recommendation: "Investigate Physical Defect",
        scanChain: "SC-005902",
        rootCause: "Metal Short",
        actionLabel: "Investigate Physical Defect",
        priority: "P0",
        priorityLabel: "Critical",
        affectedScanChain: "LOT_2_Edge",
        expectedImpact: "+2.4% yield",
        expectedYieldGainPct: 2.4,
        estimatedRuntimeReductionPct: 1.2,
        confidence: 0.91,
      },
    ],
    executiveSummary: [
      { id: "broken_chains", label: "Broken Chains", value: "7", detail: "Chains requiring Inspect Scan Chain", tone: "danger" },
      { id: "timing_debug_recs", label: "Timing Issues", value: "11", detail: "Review Capture Clock Timing recommendations", tone: "warning" },
      { id: "power_debug_recs", label: "Power Issues", value: "9", detail: "Check IR-Drop During Capture recommendations", tone: "warning" },
      { id: "constraint_violations", label: "Constraint Violations", value: "23", detail: "Review ATPG Constraints recommendations", tone: "info" },
      { id: "investigation_recs", label: "Physical Defects", value: "31", detail: "Investigate Physical Defect recommendations", tone: "primary" },
      { id: "coverage_impact", label: "Coverage Improvement", value: "+1.8%", detail: "Projected after constraint fixes", tone: "success" },
      { id: "debug_recommendations", label: "Estimated Yield Improvement", value: "+1.2%", detail: "Across active failing lots", tone: "success" },
      { id: "debug_time_saved", label: "Expected Debug Time Reduction", value: "18.4 hrs", detail: "Estimated debug hours saved", tone: "success" },
      { id: "avg_ai_confidence", label: "AI Confidence", value: "88%", detail: "DQN policy confidence", tone: "info" },
    ],
    workflow: [
      { id: "logs", label: "Failure Logs", status: "done" },
      { id: "diag", label: "Diagnosis Engine", status: "done" },
      { id: "rca", label: "Root Cause Analysis", status: "done" },
      { id: "agent", label: "Scan Debug Recommendation Agent", status: "active" },
      { id: "impl", label: "Implementation", status: "upcoming" },
      { id: "val", label: "Validation", status: "upcoming" },
    ],
  };
}
