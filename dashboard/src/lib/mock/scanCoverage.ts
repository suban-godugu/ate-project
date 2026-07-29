import { executiveOverviewKPIs } from "@/lib/scanChainData";
import type {
  CoverageDistributionTab,
  ScanCoverageDrillData,
} from "@/types/scanCoverage";

const MODULE_DIST: ScanCoverageDrillData["distributionByTab"]["Module"] = [
  { name: "M1-Core", coveragePct: 99.2, sharePct: 38.4 },
  { name: "M3-IO", coveragePct: 98.4, sharePct: 34.1 },
  { name: "M5-Cache", coveragePct: 95.8, sharePct: 27.5 },
];

const PRODUCT_DIST = [
  { name: "Orion-X", coveragePct: 98.9, sharePct: 41.2 },
  { name: "Nova-SoC", coveragePct: 97.6, sharePct: 33.8 },
  { name: "Atlas-IO", coveragePct: 96.1, sharePct: 25.0 },
];

const PATTERN_DIST = [
  { name: "PAT-ATPG-12", coveragePct: 99.4, sharePct: 36.5 },
  { name: "PAT-SCAN-08", coveragePct: 97.8, sharePct: 32.2 },
  { name: "PAT-MBIST-03", coveragePct: 95.2, sharePct: 31.3 },
];

const VECTOR_DIST = [
  { name: "VEC-128442", coveragePct: 98.7, sharePct: 40.1 },
  { name: "VEC-129018", coveragePct: 97.1, sharePct: 35.4 },
  { name: "VEC-130204", coveragePct: 96.4, sharePct: 24.5 },
];

const TESTER_DIST = [
  { name: "V93000-S1", coveragePct: 98.2, sharePct: 44.6 },
  { name: "UltraFlex-H2", coveragePct: 97.4, sharePct: 33.1 },
  { name: "J750-EX", coveragePct: 95.9, sharePct: 22.3 },
];

const WAFER_DIST = [
  { name: "W-12-044", coveragePct: 97.8, sharePct: 28.4 },
  { name: "W-12-045", coveragePct: 96.9, sharePct: 26.7 },
  { name: "W-18-019", coveragePct: 98.5, sharePct: 44.9 },
];

const distributionByTab: Record<CoverageDistributionTab, typeof MODULE_DIST> = {
  Module: MODULE_DIST,
  Product: PRODUCT_DIST,
  Pattern: PATTERN_DIST,
  Vector: VECTOR_DIST,
  Tester: TESTER_DIST,
  Wafer: WAFER_DIST,
};

/** API-ready mock payload for Scan Coverage drill page. */
export function getScanCoverageDrillData(): ScanCoverageDrillData {
  const kpi = executiveOverviewKPIs.find((item) => item.id === "scan-coverage");

  return {
    header: {
      name: "Scan Coverage",
      icon: "shield-check",
      currentValue: kpi?.value ?? "96.8%",
      statusBadge: "Monitor",
      statusVariant: "warning",
      riskLevel: "high",
      trendLabel: "+1.2% vs previous lot",
      trendDirection: "up",
      lastUpdated: new Date().toISOString(),
      activeFilters: {
        fab: "Fab-12",
        tester: "V93000-S1",
        product: "Orion-X",
        lot: "LOT-A2847",
        wafer: "W-12-044",
      },
    },
    executiveSummary: [
      {
        id: "scan-coverage",
        label: "Scan Coverage",
        value: "96.8%",
        icon: "shield-check",
        sparkline: [94.2, 94.8, 95.2, 95.6, 96.0, 96.4, 96.8],
        variant: "info",
      },
      {
        id: "target-coverage",
        label: "Target Coverage",
        value: "98.7%",
        icon: "target",
        sparkline: [98.2, 98.3, 98.4, 98.5, 98.6, 98.7, 98.7],
        variant: "default",
      },
      {
        id: "coverage-gap",
        label: "Coverage Gap",
        value: "-1.9%",
        icon: "minus-circle",
        sparkline: [-2.8, -2.5, -2.3, -2.1, -2.0, -1.9, -1.9],
        variant: "danger",
      },
      {
        id: "coverage-trend",
        label: "Coverage Trend",
        value: "+1.2%",
        icon: "trending-up",
        sparkline: [0.2, 0.4, 0.6, 0.8, 1.0, 1.1, 1.2],
        variant: "success",
      },
      {
        id: "business-impact",
        label: "Business Impact",
        value: "High",
        icon: "alert-circle",
        sparkline: [2, 2, 3, 3, 4, 4, 5],
        variant: "warning",
      },
      {
        id: "operational-status",
        label: "Operational Status",
        value: "Monitor",
        icon: "activity",
        sparkline: [1, 1, 2, 2, 2, 3, 3],
        variant: "warning",
      },
    ],
    distributionByTab,
    status: {
      fullyCovered: 92.3,
      partiallyCovered: 4.5,
      uncovered: 3.2,
      entityCount: 10000,
    },
    diagnosis: {
      confidence: 83,
      summary:
        "Overall scan coverage is stable with only a few uncovered regions remaining. Pattern optimization and ATPG improvements have increased coverage while minimizing redundant vectors. Remaining uncovered logic is isolated to low-risk modules and does not significantly affect manufacturing quality.",
      factors: [
        "High Fault Coverage",
        "High Pattern Efficiency",
        "Optimized Scan Compression",
        "Complete Module Coverage",
        "Minimal Untested Logic",
        "Stable Tester Performance",
        "Successful ATPG Optimization",
        "Balanced Pattern Distribution",
      ],
    },
    metadata: [
      { label: "Pattern ID", value: "PAT-8821" },
      { label: "Vector ID", value: "VEC-128442" },
      { label: "Scan Chain ID", value: "SC-004821" },
      { label: "ATPG Version", value: "Tessent 2024.1" },
      { label: "Coverage Type", value: "Stuck-at + Transition" },
      { label: "Coverage", value: "96.8%" },
      { label: "Diagnosis Confidence", value: "91%" },
      { label: "Compression Ratio", value: "42.8 : 1" },
    ],
    timeline: [
      { id: "upload", label: "Upload", timestamp: "09:12", status: "complete" },
      { id: "parsing", label: "Parsing", timestamp: "09:14", status: "complete" },
      { id: "validation", label: "Validation", timestamp: "09:18", status: "complete" },
      { id: "atpg", label: "ATPG Analysis", timestamp: "09:24", status: "complete" },
      { id: "calc", label: "Coverage Calculation", timestamp: "09:31", status: "running" },
      { id: "opt", label: "Optimization", timestamp: "—", status: "pending" },
      { id: "report", label: "Report Generation", timestamp: "—", status: "pending" },
      { id: "export", label: "Export", timestamp: "—", status: "pending" },
    ],
    table: {
      columns: [
        { key: "entityId", label: "Entity ID", defaultVisible: true },
        { key: "type", label: "Type", defaultVisible: true },
        { key: "metric", label: "Metric", defaultVisible: true },
        { key: "coverage", label: "Coverage", defaultVisible: true },
        { key: "delta", label: "Delta", defaultVisible: true },
        { key: "tester", label: "Tester", defaultVisible: true },
        { key: "severity", label: "Severity", defaultVisible: true },
      ],
      rows: [
        {
          entityId: "M1-Core",
          type: "Module",
          metric: "Fault Coverage",
          coverage: "99.2%",
          delta: "+0.8%",
          tester: "V93000-S1",
          severity: "Low",
        },
        {
          entityId: "M3-IO",
          type: "Module",
          metric: "Fault Coverage",
          coverage: "98.4%",
          delta: "+0.4%",
          tester: "UltraFlex-H2",
          severity: "Low",
        },
        {
          entityId: "PAT-8821",
          type: "Pattern",
          metric: "Pattern Coverage",
          coverage: "97.6%",
          delta: "+1.1%",
          tester: "V93000-S1",
          severity: "Medium",
        },
        {
          entityId: "SC-004821",
          type: "Scan Chain",
          metric: "Chain Coverage",
          coverage: "96.1%",
          delta: "-0.3%",
          tester: "J750-EX",
          severity: "Medium",
        },
        {
          entityId: "W-12-044",
          type: "Wafer",
          metric: "Die Coverage",
          coverage: "95.8%",
          delta: "+0.6%",
          tester: "V93000-S1",
          severity: "Low",
        },
        {
          entityId: "LOT-A2847",
          type: "Lot",
          metric: "Lot Coverage",
          coverage: "96.8%",
          delta: "+1.2%",
          tester: "V93000-S1",
          severity: "Low",
        },
      ],
    },
    relatedModules: [
      { id: "pattern", label: "Pattern Analysis Agent", route: "/dashboard/scan-chain?tab=pattern-analysis" },
      { id: "failure", label: "Failure Analysis Agent", route: "/dashboard/scan-chain?tab=failure-analysis" },
      { id: "diagnosis", label: "Scan Diagnosis Agent", route: "/dashboard/scan-chain?tab=scan-diagnosis" },
      { id: "recommendation", label: "Recommendation Analysis", route: "/dashboard/recommendation-analysis" },
      { id: "wafer", label: "Wafer Analysis", route: "/dashboard/wafer-analysis" },
      { id: "yield", label: "Yield Dashboard", route: "/dashboard" },
      { id: "cost", label: "Cost Intelligence", route: "/dashboard/cost-intelligence" },
      { id: "reports", label: "Reports", route: "/dashboard" },
      { id: "alerts", label: "Alerts", route: "/dashboard/alerts" },
    ],
  };
}
