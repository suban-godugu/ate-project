import type { KpiBreakdownSlice, KpiExecutiveSummaryCard, KpiRelatedModule, KpiSemiconductorMeta } from "@/types/kpiDrillDown";

export const AVG_DIAGNOSIS_CONFIDENCE_ID = "avg-diagnosis-confidence";

export interface DiagnosisConfidenceStatusData {
  high: number;
  medium: number;
  low: number;
  average: number;
}

export const DIAGNOSIS_CONFIDENCE_STATUS: DiagnosisConfidenceStatusData = {
  high: 74,
  medium: 19,
  low: 7,
  average: 91,
};

export const DIAGNOSIS_CONFIDENCE_FACTORS = [
  "Stable AI Predictions",
  "High Pattern Recognition",
  "Accurate Localization",
  "Low False Positive Rate",
  "Strong Model Consistency",
  "Reliable Tester Correlation",
  "High Historical Match Rate",
  "Validated Diagnosis Results",
] as const;

export const DIAGNOSIS_CONFIDENCE_SUMMARY =
  "AI diagnosis confidence remains consistently high across most scan chains. Recent model improvements have increased localization accuracy while reducing false positives. Remaining low-confidence predictions are limited to a small number of complex patterns and do not significantly impact manufacturing decisions.";

export const AVG_DIAGNOSIS_EXECUTIVE_SUMMARY: KpiExecutiveSummaryCard[] = [
  {
    id: "avg-confidence",
    label: "Average Diagnosis Confidence",
    value: "91%",
    icon: "shield-check",
    sparkline: [86, 87, 88, 89, 90, 90.5, 91],
    variant: "success",
  },
  {
    id: "target-confidence",
    label: "Target Confidence",
    value: "92.8%",
    icon: "target",
    sparkline: [91.8, 92.0, 92.2, 92.4, 92.6, 92.7, 92.8],
    variant: "default",
  },
  {
    id: "confidence-gap",
    label: "Confidence Gap",
    value: "-1.8%",
    icon: "minus-circle",
    sparkline: [-2.6, -2.4, -2.2, -2.0, -1.9, -1.8, -1.8],
    variant: "danger",
  },
  {
    id: "confidence-trend",
    label: "Confidence Trend",
    value: "+2.1%",
    icon: "trending-up",
    sparkline: [0.4, 0.8, 1.2, 1.5, 1.8, 2.0, 2.1],
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
];

export const AVG_DIAGNOSIS_BREAKDOWN_DIMENSIONS = [
  "scanChain",
  "module",
  "tester",
  "pattern",
  "product",
  "wafer",
] as const;

export type AvgDiagnosisBreakdownDimension = (typeof AVG_DIAGNOSIS_BREAKDOWN_DIMENSIONS)[number];

export const AVG_DIAGNOSIS_BREAKDOWN_LABELS: Record<AvgDiagnosisBreakdownDimension, string> = {
  scanChain: "Scan Chain",
  module: "Module",
  tester: "Tester",
  pattern: "Pattern",
  product: "Product",
  wafer: "Wafer",
};

export const AVG_DIAGNOSIS_BREAKDOWNS: Record<AvgDiagnosisBreakdownDimension, KpiBreakdownSlice[]> = {
  scanChain: [
    { dimension: "scanChain", label: "SC-004821", value: 94, share: 32, trend: 3.3 },
    { dimension: "scanChain", label: "SC-007892", value: 91, share: 28, trend: 1.8 },
    { dimension: "scanChain", label: "SC-003156", value: 88, share: 24, trend: -0.6 },
  ],
  module: [
    { dimension: "module", label: "M1-Core", value: 95, share: 38, trend: 2.4 },
    { dimension: "module", label: "M3-IO", value: 92, share: 34, trend: 1.6 },
    { dimension: "module", label: "M5-Cache", value: 87, share: 28, trend: -1.2 },
  ],
  tester: [
    { dimension: "tester", label: "V93000-S1", value: 93, share: 42, trend: 2.8 },
    { dimension: "tester", label: "UltraFlex-H2", value: 90, share: 33, trend: 1.1 },
    { dimension: "tester", label: "J750-EX", value: 86, share: 25, trend: -0.9 },
  ],
  pattern: [
    { dimension: "pattern", label: "PAT-8821", value: 94, share: 36, trend: 3.1 },
    { dimension: "pattern", label: "PAT-4821", value: 91, share: 31, trend: 1.4 },
    { dimension: "pattern", label: "PAT-7892", value: 87, share: 33, trend: -0.7 },
  ],
  product: [
    { dimension: "product", label: "Orion-X", value: 93, share: 41, trend: 2.6 },
    { dimension: "product", label: "Nova-SoC", value: 90, share: 35, trend: 1.3 },
    { dimension: "product", label: "Atlas-IO", value: 86, share: 24, trend: -0.5 },
  ],
  wafer: [
    { dimension: "wafer", label: "W-12-044", value: 92, share: 29, trend: 2.0 },
    { dimension: "wafer", label: "W-12-045", value: 89, share: 27, trend: 0.8 },
    { dimension: "wafer", label: "W-18-019", value: 94, share: 44, trend: 3.3 },
  ],
};

export const AVG_DIAGNOSIS_SEMICONDUCTOR_META: KpiSemiconductorMeta = {
  patternId: "PAT-8821",
  vectorId: "VEC-128442",
  scanChainId: "SC-004821",
  aiModelVersion: "Verilumen AI v2.4",
  diagnosisType: "Cell Aware",
  diagnosisConfidence: "91%",
  validationScore: "94%",
  compressionRatio: "42.8 : 1",
};

export const AVG_DIAGNOSIS_META_LABELS: Record<string, string> = {
  patternId: "Pattern ID",
  vectorId: "Vector ID",
  scanChainId: "Scan Chain ID",
  aiModelVersion: "AI Model Version",
  diagnosisType: "Diagnosis Type",
  diagnosisConfidence: "Diagnosis Confidence",
  validationScore: "Validation Score",
  compressionRatio: "Compression Ratio",
};

export const AVG_DIAGNOSIS_RELATED_MODULES: KpiRelatedModule[] = [
  { id: "pattern", label: "Pattern Analysis Agent", route: "/dashboard/scan-chain?tab=pattern-analysis" },
  { id: "failure", label: "Failure Analysis Agent", route: "/dashboard/scan-chain?tab=failure-analysis" },
  { id: "diagnosis", label: "Scan Diagnosis Agent", route: "/dashboard/scan-chain?tab=scan-diagnosis" },
  { id: "recommendation", label: "Recommendation Analysis", route: "/dashboard/recommendation-analysis" },
  { id: "wafer", label: "Wafer Analysis", route: "/dashboard/wafer-analysis" },
  { id: "yield", label: "Yield Dashboard", route: "/dashboard" },
  { id: "cost", label: "Cost Intelligence", route: "/dashboard/cost-intelligence" },
  { id: "reports", label: "Reports", route: "/dashboard" },
  { id: "alerts", label: "Alerts", route: "/dashboard/alerts" },
];

export const AVG_DIAGNOSIS_TABLE_ROWS = [
  {
    id: "row-1",
    entityId: "SC-004821",
    entityType: "Scan Chain",
    metric: "Localization Confidence",
    diagnosisConfidence: "94%",
    delta: "+3.3%",
    tester: "V93000-S1",
    severity: "Low",
  },
  {
    id: "row-2",
    entityId: "M1-Core",
    entityType: "Module",
    metric: "Module Confidence",
    diagnosisConfidence: "95%",
    delta: "+2.4%",
    tester: "UltraFlex-H2",
    severity: "Low",
  },
  {
    id: "row-3",
    entityId: "PAT-8821",
    entityType: "Pattern",
    metric: "Pattern Confidence",
    diagnosisConfidence: "94%",
    delta: "+3.1%",
    tester: "V93000-S1",
    severity: "Low",
  },
  {
    id: "row-4",
    entityId: "W-12-044",
    entityType: "Wafer",
    metric: "Wafer Confidence",
    diagnosisConfidence: "92%",
    delta: "+2.0%",
    tester: "V93000-S1",
    severity: "Low",
  },
  {
    id: "row-5",
    entityId: "M5-Cache",
    entityType: "Module",
    metric: "Module Confidence",
    diagnosisConfidence: "87%",
    delta: "-1.2%",
    tester: "J750-EX",
    severity: "Medium",
  },
  {
    id: "row-6",
    entityId: "PAT-7892",
    entityType: "Pattern",
    metric: "Pattern Confidence",
    diagnosisConfidence: "87%",
    delta: "-0.7%",
    tester: "J750-EX",
    severity: "Medium",
  },
];
