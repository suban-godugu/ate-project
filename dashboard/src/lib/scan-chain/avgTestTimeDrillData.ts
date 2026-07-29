import type { KpiBreakdownSlice, KpiExecutiveSummaryCard, KpiRelatedModule, KpiSemiconductorMeta } from "@/types/kpiDrillDown";

export const AVG_TEST_TIME_ID = "avg-test-time";

export interface TestTimeDistributionItem {
  name: string;
  avgSeconds: number;
  sharePct: number;
}

export interface TestTimeStatusData {
  optimal: number;
  acceptable: number;
  slow: number;
  averageSeconds: number;
  totalSamples: number;
}

export const TEST_TIME_STATUS: TestTimeStatusData = {
  optimal: 71,
  acceptable: 22,
  slow: 7,
  averageSeconds: 18.4,
  totalSamples: 12480,
};

export const TEST_TIME_PERFORMANCE_FACTORS = [
  "Optimized Tester Scheduling",
  "Reduced Idle Time",
  "Balanced Pattern Distribution",
  "Efficient Vector Execution",
  "Stable Tester Performance",
  "Parallel Test Execution",
  "Reduced Retest Rate",
  "High Throughput",
] as const;

export const TEST_TIME_ANALYSIS_SUMMARY =
  "Average test time remains within acceptable production limits. Parallel scheduling, optimized ATPG vectors, and balanced tester utilization have reduced idle time and improved execution efficiency. A small number of products continue to require longer execution cycles due to increased pattern complexity.";

export const AVG_TEST_TIME_EXECUTIVE_SUMMARY: KpiExecutiveSummaryCard[] = [
  {
    id: "avg-test-time",
    label: "Average Test Time",
    value: "18.4 s",
    icon: "timer",
    sparkline: [21, 20.5, 20, 19.5, 19, 18.8, 18.4],
    variant: "info",
  },
  {
    id: "target-test-time",
    label: "Target Test Time",
    value: "17.7 s",
    icon: "target",
    sparkline: [18.2, 18.0, 17.9, 17.8, 17.8, 17.7, 17.7],
    variant: "default",
  },
  {
    id: "time-delta",
    label: "Time Delta",
    value: "+0.7 s",
    icon: "git-compare",
    sparkline: [1.2, 1.1, 1.0, 0.9, 0.8, 0.7, 0.7],
    variant: "warning",
  },
  {
    id: "trend",
    label: "Trend",
    value: "-3.1%",
    icon: "trending-down",
    sparkline: [-0.5, -1.0, -1.5, -2.0, -2.5, -2.9, -3.1],
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

export const TEST_TIME_DISTRIBUTION_TABS = [
  "tester",
  "product",
  "module",
  "pattern",
  "vector",
  "wafer",
  "lot",
] as const;

export type TestTimeDistributionTab = (typeof TEST_TIME_DISTRIBUTION_TABS)[number];

export const TEST_TIME_DISTRIBUTION_LABELS: Record<TestTimeDistributionTab, string> = {
  tester: "Tester",
  product: "Product",
  module: "Module",
  pattern: "Pattern",
  vector: "Vector",
  wafer: "Wafer",
  lot: "Lot",
};

export const TEST_TIME_DISTRIBUTION_BY_TAB: Record<TestTimeDistributionTab, TestTimeDistributionItem[]> = {
  tester: [
    { name: "ATE-02", avgSeconds: 18.8, sharePct: 34.2 },
    { name: "ATE-01", avgSeconds: 18.2, sharePct: 33.1 },
    { name: "ATE-03", avgSeconds: 17.9, sharePct: 32.7 },
  ],
  product: [
    { name: "Orion-X", avgSeconds: 18.6, sharePct: 41.4 },
    { name: "Nova-SoC", avgSeconds: 18.3, sharePct: 35.2 },
    { name: "Atlas-IO", avgSeconds: 17.8, sharePct: 23.4 },
  ],
  module: [
    { name: "M1-Core", avgSeconds: 18.5, sharePct: 38.6 },
    { name: "M3-IO", avgSeconds: 18.1, sharePct: 34.8 },
    { name: "M5-Cache", avgSeconds: 17.6, sharePct: 26.6 },
  ],
  pattern: [
    { name: "PAT-8821", avgSeconds: 19.1, sharePct: 36.5 },
    { name: "PAT-4821", avgSeconds: 18.4, sharePct: 33.8 },
    { name: "PAT-7892", avgSeconds: 17.9, sharePct: 29.7 },
  ],
  vector: [
    { name: "VEC-128442", avgSeconds: 18.7, sharePct: 40.2 },
    { name: "VEC-129018", avgSeconds: 18.2, sharePct: 34.1 },
    { name: "VEC-130204", avgSeconds: 17.8, sharePct: 25.7 },
  ],
  wafer: [
    { name: "W-12-044", avgSeconds: 18.5, sharePct: 28.8 },
    { name: "W-12-045", avgSeconds: 18.1, sharePct: 26.4 },
    { name: "W-18-019", avgSeconds: 18.8, sharePct: 44.8 },
  ],
  lot: [
    { name: "LOT-A2847", avgSeconds: 18.4, sharePct: 40.5 },
    { name: "LOT-B2848", avgSeconds: 18.0, sharePct: 33.3 },
    { name: "LOT-C2849", avgSeconds: 17.7, sharePct: 26.2 },
  ],
};

export const AVG_TEST_TIME_BREAKDOWN_DIMENSIONS = [
  "tester",
  "pattern",
  "lot",
  "vector",
  "product",
  "module",
] as const;

export type AvgTestTimeBreakdownDimension = (typeof AVG_TEST_TIME_BREAKDOWN_DIMENSIONS)[number];

export const AVG_TEST_TIME_BREAKDOWN_LABELS: Record<AvgTestTimeBreakdownDimension, string> = {
  tester: "Tester",
  pattern: "Pattern",
  lot: "Lot",
  vector: "Vector",
  product: "Product",
  module: "Module",
};

export const AVG_TEST_TIME_BREAKDOWNS: Record<AvgTestTimeBreakdownDimension, KpiBreakdownSlice[]> = {
  tester: [
    { dimension: "tester", label: "ATE-01", value: 18.2, share: 34, trend: -2.1 },
    { dimension: "tester", label: "ATE-02", value: 18.8, share: 33, trend: 1.4 },
    { dimension: "tester", label: "ATE-03", value: 17.9, share: 33, trend: -3.2 },
  ],
  pattern: [
    { dimension: "pattern", label: "PAT-8821", value: 19.1, share: 37, trend: 2.3 },
    { dimension: "pattern", label: "PAT-4821", value: 18.4, share: 34, trend: -1.1 },
    { dimension: "pattern", label: "PAT-7892", value: 17.9, share: 29, trend: -2.4 },
  ],
  lot: [
    { dimension: "lot", label: "LOT-A2847", value: 18.4, share: 41, trend: -2.8 },
    { dimension: "lot", label: "LOT-B2848", value: 18.0, share: 33, trend: -1.6 },
    { dimension: "lot", label: "LOT-C2849", value: 17.7, share: 26, trend: -3.5 },
  ],
  vector: [
    { dimension: "vector", label: "VEC-128442", value: 18.7, share: 40, trend: 1.2 },
    { dimension: "vector", label: "VEC-129018", value: 18.2, share: 34, trend: -1.8 },
    { dimension: "vector", label: "VEC-130204", value: 17.8, share: 26, trend: -2.6 },
  ],
  product: [
    { dimension: "product", label: "Orion-X", value: 18.6, share: 41, trend: 0.8 },
    { dimension: "product", label: "Nova-SoC", value: 18.3, share: 35, trend: -1.4 },
    { dimension: "product", label: "Atlas-IO", value: 17.8, share: 24, trend: -3.0 },
  ],
  module: [
    { dimension: "module", label: "M1-Core", value: 18.5, share: 39, trend: -0.6 },
    { dimension: "module", label: "M3-IO", value: 18.1, share: 35, trend: -2.2 },
    { dimension: "module", label: "M5-Cache", value: 17.6, share: 26, trend: -3.8 },
  ],
};

export const AVG_TEST_TIME_SEMICONDUCTOR_META: KpiSemiconductorMeta = {
  patternId: "PAT-8821",
  vectorId: "VEC-128442",
  scanChainId: "SC-004821",
  atpgVersion: "Tessent 2024.1",
  tester: "ATE-01",
  averageTestTime: "18.4 s",
  throughput: "96.4%",
  compressionRatio: "42.8 : 1",
};

export const AVG_TEST_TIME_META_LABELS: Record<string, string> = {
  patternId: "Pattern ID",
  vectorId: "Vector ID",
  scanChainId: "Scan Chain ID",
  atpgVersion: "ATPG Version",
  tester: "Tester",
  averageTestTime: "Average Test Time",
  throughput: "Throughput",
  compressionRatio: "Compression Ratio",
};

export const AVG_TEST_TIME_RELATED_MODULES: KpiRelatedModule[] = [
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

export const AVG_TEST_TIME_TABLE_ROWS = [
  {
    id: "row-1",
    entityId: "ATE-01",
    entityType: "Tester",
    metric: "Execution Time",
    averageTestTime: "18.2 s",
    delta: "-2.1%",
    tester: "ATE-01",
    severity: "Low",
  },
  {
    id: "row-2",
    entityId: "PAT-8821",
    entityType: "Pattern",
    metric: "Pattern Runtime",
    averageTestTime: "19.1 s",
    delta: "+2.3%",
    tester: "ATE-02",
    severity: "Medium",
  },
  {
    id: "row-3",
    entityId: "LOT-A2847",
    entityType: "Lot",
    metric: "Lot Runtime",
    averageTestTime: "18.4 s",
    delta: "-2.8%",
    tester: "ATE-01",
    severity: "Low",
  },
  {
    id: "row-4",
    entityId: "VEC-128442",
    entityType: "Vector",
    metric: "Vector Runtime",
    averageTestTime: "18.7 s",
    delta: "+1.2%",
    tester: "ATE-02",
    severity: "Low",
  },
  {
    id: "row-5",
    entityId: "M5-Cache",
    entityType: "Module",
    metric: "Module Runtime",
    averageTestTime: "17.6 s",
    delta: "-3.8%",
    tester: "ATE-03",
    severity: "Low",
  },
  {
    id: "row-6",
    entityId: "Orion-X",
    entityType: "Product",
    metric: "Product Runtime",
    averageTestTime: "18.6 s",
    delta: "+0.8%",
    tester: "ATE-01",
    severity: "Medium",
  },
];
