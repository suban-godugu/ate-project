/** Minimal KPI shape consumed by drill-down workspace builder. */
export interface DrillDownKPI {
  id: string;
  title: string;
  value: string;
  subtitle?: string;
  change: number;
  trend: "up" | "down";
  sparkline: number[];
  icon: string;
  positiveIsGood?: boolean;
}

export type KpiWorkspaceLayoutPreset = "standard" | "failure" | "diagnosis" | "optimization" | "debug";

export type KpiWorkspaceModule =
  | "executive"
  | "pattern"
  | "failure"
  | "diagnosis"
  | "recommendation"
  | "testOptimization"
  | "scanDebug";

export const WORKSPACE_LAYOUT_CLASS: Record<KpiWorkspaceLayoutPreset, string> = {
  standard: "flex h-[90vh] w-[90vw] max-w-[1800px] flex-col overflow-hidden rounded-2xl border border-[rgba(139,92,246,0.25)] bg-[#0B0F1A]/95 shadow-2xl shadow-purple-900/25 backdrop-blur-xl",
  failure: "flex h-[92vh] w-[95vw] max-w-[1920px] flex-col overflow-hidden rounded-2xl border border-[rgba(139,92,246,0.25)] bg-[#0B0F1A]/95 shadow-2xl shadow-purple-900/25 backdrop-blur-xl",
  diagnosis: "flex h-[92vh] w-[95vw] max-w-[1920px] flex-col overflow-hidden rounded-2xl border border-[rgba(139,92,246,0.25)] bg-[#0B0F1A]/95 shadow-2xl shadow-purple-900/25 backdrop-blur-xl",
  optimization: "flex h-[92vh] w-[95vw] max-w-[1920px] flex-col overflow-hidden rounded-2xl border border-[rgba(139,92,246,0.25)] bg-[#0B0F1A]/95 shadow-2xl shadow-purple-900/25 backdrop-blur-xl",
  debug: "flex h-[92vh] w-[95vw] max-w-[1920px] flex-col overflow-hidden rounded-2xl border border-[rgba(139,92,246,0.25)] bg-[#0B0F1A]/95 shadow-2xl shadow-purple-900/25 backdrop-blur-xl",
};

export type KpiRiskLevel = "critical" | "high" | "medium" | "low" | "nominal";
export type KpiTrendTab = "24h" | "7d" | "30d" | "90d" | "prev-lot" | "prev-release";
export type KpiChartKind = "line" | "area" | "bar" | "scatter";
export type KpiWidgetType =
  | "line"
  | "area"
  | "bar"
  | "scatter"
  | "heatmap"
  | "wafer-map"
  | "gauge"
  | "histogram"
  | "pareto"
  | "stacked-bar"
  | "radar"
  | "correlation-matrix"
  | "similarity-matrix"
  | "network"
  | "timeline-mini"
  | "distribution"
  | "sankey"
  | "bubble"
  | "treemap"
  | "cluster";

export interface KpiDrillDownFilters {
  fab: string;
  site: string;
  tester: string;
  handler: string;
  product: string;
  package: string;
  lot: string;
  wafer: string;
  die: string;
  module: string;
  scanChain: string;
  pattern: string;
  vector: string;
  timeRange: string;
}

export interface KpiWorkspaceHeader {
  kpiId: string;
  icon: string;
  name: string;
  currentValue: string;
  statusBadge: string;
  statusVariant: "success" | "warning" | "danger" | "info";
  trendLabel: string;
  trendDirection: "up" | "down" | "flat";
  riskLevel: KpiRiskLevel;
  lastUpdated: string;
  diagnosisConfidence?: string;
  recommendationStatus?: string;
  recommendationPriority?: string;
  recommendationVersion?: string;
  aiVersion?: string;
  activeFilters: Pick<KpiDrillDownFilters, "fab" | "tester" | "product" | "lot" | "wafer">;
}

export interface KpiExecutiveSummaryCard {
  id: string;
  label: string;
  value: string;
  icon: string;
  sparkline: number[];
  variant?: "default" | "success" | "warning" | "danger" | "info";
}

export interface KpiTrendSeries {
  label: string;
  value: number;
  value2?: number;
}

export interface KpiTrendAnalytics {
  chartKind: KpiChartKind;
  series: KpiTrendSeries[];
  comparisonLabel?: string;
}

export interface KpiWidgetSpec {
  id: string;
  type: KpiWidgetType;
  title: string;
  span: 1 | 2;
  height: number;
  data: Record<string, unknown>;
}

export interface KpiRootCause {
  primaryCause: string;
  confidence: number;
  affectedModules: string[];
  affectedPatterns: string[];
  affectedChains: string[];
  affectedLots: string[];
  affectedWafers: string[];
  severity: KpiRiskLevel;
  risk: KpiRiskLevel;
  priority?: "P0" | "P1" | "P2" | "P3";
  expectedYieldImpact: string;
  expectedCostImpact?: string;
  failureType?: string;
  affectedScanCells?: string[];
  clockDomain?: string;
  shiftCycle?: string;
  captureCycle?: string;
  faultModel?: string;
  compressionRatio?: string;
  suspectedPhysicalRegion?: string;
}

export interface KpiRecommendation {
  id: string;
  action: string;
  priority: "P0" | "P1" | "P2" | "P3";
  estimatedImprovement: string;
  runtimeSaving: string;
  costSaving: string;
  confidence: number;
}

export interface KpiBreakdownSlice {
  dimension: string;
  label: string;
  value: number;
  share: number;
  trend: number;
}

export interface KpiTimelineEvent {
  id: string;
  type:
    | "upload"
    | "parsing"
    | "validation"
    | "embedding"
    | "execution"
    | "failure-detection"
    | "diagnosis"
    | "ai-analysis"
    | "recommendation"
    | "report"
    | "export";
  label: string;
  timestamp: string;
  status: "complete" | "running" | "failed" | "pending";
}

export interface KpiTableColumn {
  key: string;
  label: string;
  frozen?: boolean;
  defaultVisible?: boolean;
}

export interface KpiTableRow {
  id: string;
  [key: string]: string | number;
}

export interface KpiRelatedModule {
  id: string;
  label: string;
  route: string;
  badge?: string;
}

export interface KpiSemiconductorMeta {
  patternId?: string;
  vectorId?: string;
  scanChainId?: string;
  scanCell?: string;
  flopId?: string;
  compressionRatio?: string;
  atpgVersion?: string;
  tester?: string;
  programVersion?: string;
  failBin?: string;
  defectClass?: string;
  clockDomain?: string;
  faultModel?: string;
  coverage?: string;
  diagnosisConfidence?: string;
  diagnosisType?: string;
  aiModelVersion?: string;
  validationScore?: string;
  averageTestTime?: string;
  throughput?: string;
  recommendationScore?: string;
  engineerApproval?: string;
  yield?: string;
  runtime?: string;
  power?: string;
  cost?: string;
  riskScore?: string;
  roi?: string;
}

export interface KpiTraceabilityNode {
  id: string;
  label: string;
  value: string;
}

export interface KpiTopologyNode {
  id: string;
  label: string;
  status: "broken" | "failing-cell" | "debug" | "warning" | "healthy";
}

export interface KpiTopologyEdge {
  from: string;
  to: string;
  broken?: boolean;
}

export interface KpiAiDecisionOverview {
  category: string;
  reason: string;
  optimizationGoal: string;
  historicalSuccessRate: string;
  similarCases: number;
  engineeringBenefit: string;
  businessBenefit: string;
  confidence: number;
  implementationDifficulty: string;
  riskLevel: KpiRiskLevel;
}

export interface KpiFeatureImportance {
  feature: string;
  weight: number;
}

export interface KpiAiExplanation {
  recommendationReason: string;
  featureImportance: KpiFeatureImportance[];
  similarCases: string[];
  alternative: string;
  riskAnalysis: string;
  expectedOutcome: string;
  confidence: number;
}

export interface KpiImpactMetric {
  label: string;
  before: string;
  after: string;
  delta: string;
}

export interface KpiExpectedImpactCard {
  label: string;
  value: string;
  delta: string;
  variant?: "default" | "success" | "warning" | "danger" | "info";
}

export interface KpiApprovalAction {
  id: string;
  label: string;
  description: string;
  impactHint: string;
  variant?: "primary" | "outline" | "danger";
}

export interface KpiWorkspaceFooter {
  recordCount: number;
  lastRefresh: string;
  backendStatus: "online" | "degraded" | "offline";
  databaseStatus: "connected" | "slow" | "disconnected";
  parserVersion: string;
  aiModelVersion: string;
  latencyMs: number;
}

export interface KpiWorkspaceData {
  kpi: DrillDownKPI;
  module: KpiWorkspaceModule;
  layoutPreset: KpiWorkspaceLayoutPreset;
  breakdownDimensions: readonly string[];
  copilotSuggestions: string[];
  trendTabOptions: readonly { id: KpiTrendTab; label: string }[];
  topologyFirst: boolean;
  traceability: KpiTraceabilityNode[];
  topologyGraph: { nodes: KpiTopologyNode[]; edges: KpiTopologyEdge[] };
  aiDecision?: KpiAiDecisionOverview;
  aiExplanation?: KpiAiExplanation;
  expectedImpactMetrics?: KpiExpectedImpactCard[];
  simulationMetrics?: KpiImpactMetric[];
  approvalActions?: KpiApprovalAction[];
  header: KpiWorkspaceHeader;
  executiveSummary: KpiExecutiveSummaryCard[];
  trendAnalytics: Record<KpiTrendTab, KpiTrendAnalytics>;
  widgets: KpiWidgetSpec[];
  breakdowns: Record<string, KpiBreakdownSlice[]>;
  rootCause: KpiRootCause;
  recommendations: KpiRecommendation[];
  timeline: KpiTimelineEvent[];
  table: { columns: KpiTableColumn[]; rows: KpiTableRow[] };
  relatedModules: KpiRelatedModule[];
  semiconductorMeta: KpiSemiconductorMeta;
  footer: KpiWorkspaceFooter;
}

export interface KpiWorkspaceApiResponse {
  kpiId: string;
  profileId: string;
  workspace: Omit<KpiWorkspaceData, "kpi">;
}

export const KPI_BREAKDOWN_DIMENSIONS = [
  "fab",
  "tester",
  "product",
  "lot",
  "wafer",
  "module",
  "pattern",
  "scanChain",
  "vector",
] as const;

export const FAILURE_BREAKDOWN_DIMENSIONS = [
  "tester",
  "lot",
  "wafer",
  "module",
  "die",
  "pattern",
  "scanChain",
  "failureBin",
  "rootCause",
] as const;

export const DIAGNOSIS_BREAKDOWN_DIMENSIONS = [
  "fab",
  "tester",
  "lot",
  "wafer",
  "die",
  "pattern",
  "scanChain",
  "scanCell",
  "flop",
] as const;

export const DIAGNOSIS_TREND_TABS: { id: KpiTrendTab; label: string }[] = [
  { id: "24h", label: "24 Hours" },
  { id: "7d", label: "7 Days" },
  { id: "30d", label: "30 Days" },
  { id: "prev-lot", label: "Previous Lot" },
  { id: "90d", label: "Previous Wafer" },
  { id: "prev-release", label: "Release Comparison" },
];

export const RECOMMENDATION_BREAKDOWN_DIMENSIONS = [
  "product",
  "tester",
  "lot",
  "wafer",
  "patternGroup",
  "pattern",
  "faultModel",
  "coverage",
  "compression",
  "runtime",
] as const;

export const TEST_OPT_BREAKDOWN_DIMENSIONS = [
  "fab",
  "tester",
  "site",
  "lot",
  "wafer",
  "product",
  "package",
  "device",
  "testFlow",
  "testProgram",
] as const;

export const SCAN_DEBUG_BREAKDOWN_DIMENSIONS = [
  "tester",
  "lot",
  "wafer",
  "pattern",
  "scanChain",
  "module",
  "clockDomain",
  "faultModel",
  "powerDomain",
] as const;

export type KpiBreakdownDimension = (typeof KPI_BREAKDOWN_DIMENSIONS)[number];

export const KPI_TREND_TABS: { id: KpiTrendTab; label: string }[] = [
  { id: "24h", label: "24 Hours" },
  { id: "7d", label: "7 Days" },
  { id: "30d", label: "30 Days" },
  { id: "90d", label: "90 Days" },
  { id: "prev-lot", label: "Compare Previous Lot" },
  { id: "prev-release", label: "Compare Previous Release" },
];
