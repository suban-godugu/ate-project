export type KpiSeverity = "critical" | "high" | "medium" | "low" | "info";
export type KpiStatus = "on_track" | "at_risk" | "breach" | "improving" | "stable";
export type RecommendationStatus =
  | "pending"
  | "in_review"
  | "approved"
  | "rejected"
  | "assigned";
export type RecommendationCategory =
  | "SCAN_CHAIN_DEBUG"
  | "TIMING_DEBUG"
  | "POWER_RELATED_DEBUG"
  | "ATPG_CONSTRAINT_REVIEW"
  | "PHYSICAL_DEFECT_INVESTIGATION";
export type RecommendationPriority = "P0" | "P1" | "P2" | "P3";

export type ScanDebugKpiId =
  | "broken_chains"
  | "debug_recommendations"
  | "avg_ai_confidence"
  | "constraint_violations"
  | "pending_review"
  | "coverage_impact"
  | "timing_violations"
  | "timing_debug_recs"
  | "worst_slack"
  | "power_violations"
  | "power_debug_recs"
  | "peak_switching"
  | "defect_suspects"
  | "investigation_recs"
  | "defect_localization";

export type KpiSectionId =
  | "scan_chain_debug"
  | "atpg_constraint_review"
  | "timing_debug"
  | "power_related_debug"
  | "physical_defect_investigation";

export interface SparkPoint {
  t: string;
  v: number;
}

export interface KpiCardModel {
  id: ScanDebugKpiId;
  section: KpiSectionId;
  title: string;
  value: string | number;
  target: string | number;
  trendPct: number;
  sparkline: number[];
  status: KpiStatus;
  severity: KpiSeverity;
  tooltip: string;
}

export interface RecommendationRow {
  id: string;
  category: RecommendationCategory;
  categoryLabel?: string;
  actionLabel?: string;
  recommendation?: string;
  scanChain?: string;
  rootCause?: string;
  priority: RecommendationPriority;
  priorityLabel?: string;
  affectedScanChain: string;
  expectedImpact?: string;
  expectedYieldGainPct: number;
  estimatedRuntimeReductionPct: number;
  confidence: number;
  lotId?: string;
  dieLabel?: string;
}

export interface ExecutiveSummaryCard {
  id: string;
  label: string;
  value: string;
  detail: string;
  tone: "primary" | "success" | "warning" | "danger" | "info";
}

export interface ChartSlice {
  name: string;
  value: number;
  fill?: string;
}

export interface TrendPoint {
  date: string;
  value: number;
  approved?: number;
  rejected?: number;
  pending?: number;
}

export interface WorkflowStep {
  id: string;
  label: string;
  status: "done" | "active" | "upcoming";
}

export interface DecisionPanelData {
  executiveSummary: string;
  rootCause: string;
  confidence: number;
  businessImpact: string;
  risk: string;
  recommendation: string;
  whatFailed: string;
  whyAiRecommended: string;
  whatImproves: string;
  shouldApprove: string;
}

export interface VizSeries {
  label: string;
  value: number;
}

export interface EngineeringImpactMetric {
  label: string;
  before: string;
  after: string;
  delta: string;
}

export interface RawEngineeringRow {
  pattern: string;
  chain: string;
  vector: string;
  cell: string;
  clock: string;
  coverage: number;
  fault: string;
  runtimeMs: number;
  powerMw: number;
  confidence: number;
  recommendationScore: number;
  recommendedAction?: string;
  breakIsolationResult?: string;
}

export interface ChainBreakDiagnosisResult {
  lotId?: string;
  dieLabel?: string;
  chain?: string;
  chainName?: string;
  result: string;
  candidateBit?: number | null;
  segmentStart?: number | null;
  segmentEnd?: number | null;
  cellLabel?: string;
  candidateCell?: string;
  locationStatus?: string;
  scanIn?: string;
  scanOut?: string;
  scanLength?: number;
  failCount?: number;
  howToImplement?: string;
  faultType?: string;
  diagnosisRank?: number;
  historicalMatchCount?: number;
  historicalSimilarity?: number;
  historicalRootCause?: string;
  closestHistoricalCell?: string;
  chainNumber?: number | null;
}

export interface TimelineEvent {
  id: string;
  label: string;
  at: string;
  status: "done" | "active" | "upcoming";
}

export interface CopilotMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ConstraintViolationDiagnosisResult {
  result: string;
  rank?: number;
  lotId?: string;
  dieLabel?: string;
  heldPins?: string;
  allHeldPins?: string;
  fanoutSignal?: string;
  failingPatternCount?: number;
  totalFailingPatterns?: number;
  failingChannelObservations?: number;
  procedure?: string;
  patternLabels?: string[];
  lotDifferentialPatterns?: number;
  usedLotDifferential?: boolean;
  suspectedOverConstraint?: boolean;
  affectedDies?: number;
  constraintCategory?: string;
  constraintCategoryLabel?: string;
  constraintPin?: string;
  constraintValue?: string;
}

export interface ConstraintReviewRecDiagnosisResult {
  result: string;
  rank?: number;
  lotId?: string;
  dieLabel?: string;
  heldPins?: string;
  fanoutSignal?: string;
  failingPatternCount?: number;
  procedure?: string;
  patternLabels?: string[];
  affectedDies?: number;
  chainsAffected?: number;
  totalChains?: number;
  constraintCategory?: string;
  constraintCategoryLabel?: string;
  constraintPin?: string;
  constraintValue?: string;
  historicalMatchCount?: number;
  historicalResolution?: string;
  recommendedAction?: string;
  recommendDetail?: string;
  suspectedOverConstraint?: boolean;
}

export interface CoverageImpactDiagnosisResult {
  result: string;
  rank?: number;
  lotId?: string;
  dieLabel?: string;
  heldPins?: string;
  fanoutSignal?: string;
  signature?: string;
  coverageImpactPct?: number;
  associatedPatterns?: number;
  totalFailingPatterns?: number;
  constraintCategory?: string;
  constraintCategoryLabel?: string;
  patternLabels?: string[];
  affectedDies?: number;
  estimateOnly?: boolean;
  scope?: string;
}

export interface TimingViolationDiagnosisResult {
  result: string;
  rank?: number;
  lotId?: string;
  dieLabel?: string;
  patternId?: string;
  patternLabel?: string;
  timingChain?: string;
  timingFlop?: string;
  kind?: string;
  classification?: string;
  worstSlackPs?: number;
  setupSlackPs?: number;
  holdSlackPs?: number;
  fastFrequencyMhz?: number;
  slowFrequencyMhz?: number;
  captureEdgeSpacingNs?: number;
  nearMinimumMargin?: boolean;
  fastTimingSet?: string;
  slowTimingSet?: string;
  multiInsertionObserved?: boolean;
  atSpeedCorrelated?: boolean;
}

export interface TimingDebugRecDiagnosisResult {
  result: string;
  rank?: number;
  lotId?: string;
  dieLabel?: string;
  patternId?: string;
  patternLabel?: string;
  timingChain?: string;
  timingFlop?: string;
  clockDomain?: string;
  kind?: string;
  classification?: string;
  worstSlackPs?: number;
  historicalMatchCount?: number;
  historicalCite?: string;
  recommendedAction?: string;
  recommendDetail?: string;
  diagnosisTransitionPathDelay?: boolean;
  fastFrequencyMhz?: number;
  captureEdgeSpacingNs?: number;
}

export interface WorstSlackDiagnosisResult {
  result: string;
  rank?: number;
  lotId?: string;
  dieLabel?: string;
  patternId?: string;
  patternLabel?: string;
  timingChain?: string;
  timingFlop?: string;
  kind?: string;
  worstSlackPs?: number;
  failFrequencyMhz?: number;
  passFrequencyMhz?: number;
  frequencyMarginPct?: number;
}

export interface PowerViolationDiagnosisResult {
  result: string;
  rank?: number;
  lotId?: string;
  dieLabel?: string;
  patternId?: string;
  patternLabel?: string;
  irDropMv?: number;
  thermalC?: number;
  status?: string;
  kind?: string;
  flaggedDespitePass?: boolean;
  irThresholdMv?: number;
  thermalThresholdC?: number;
}

export interface PowerDebugRecDiagnosisResult {
  result: string;
  rank?: number;
  lotId?: string;
  dieLabel?: string;
  patternId?: string;
  patternLabel?: string;
  irDropMv?: number;
  thermalC?: number;
  status?: string;
  kind?: string;
  pctAboveThreshold?: number;
  flaggedDespitePass?: boolean;
  irThresholdMv?: number;
  thermalThresholdC?: number;
  historicalMatchCount?: number;
  historicalCite?: string;
  recommendedAction?: string;
  recommendDetail?: string;
}

export interface PeakSwitchingDiagnosisResult {
  result: string;
  rank?: number;
  lotId?: string;
  dieLabel?: string;
  patternId?: string;
  patternLabel?: string;
  irDropMv?: number;
  avgIrDropMv?: number;
  deltaVsAvgMv?: number;
  thermalC?: number;
  status?: string;
  isPeak?: boolean;
  recommendedAction?: string;
}

export interface DefectSuspectDiagnosisResult {
  result: string;
  rank?: number;
  diagnosisRank?: number;
  netId?: string;
  cellName?: string;
  flipFlopId?: string;
  neighborFrom?: string;
  neighborTo?: string;
  chain?: string;
  chainNumber?: number;
  bitPosition?: number;
  consistentPatterns?: number;
  totalFailingPatterns?: number;
  consistencyRatio?: number;
  confidencePct?: number;
  rootCause?: string;
  recommendedAction?: string;
}

export interface InvestigationRecDiagnosisResult {
  result: string;
  rank?: number;
  diagnosisRank?: number;
  netId?: string;
  cellName?: string;
  neighborFrom?: string;
  neighborTo?: string;
  chain?: string;
  rootCause?: string;
  faultHypothesis?: string;
  transitionFaultCount?: number;
  irDropMv?: number;
  irThresholdMv?: number;
  powerInducedRuledOut?: boolean;
  historicalMatchCount?: number;
  historicalCite?: string;
  pfaTechnique?: string;
  recommendedAction?: string;
  consistentPatterns?: number;
  totalFailingPatterns?: number;
  confidencePct?: number;
}

export interface DefectLocalizationDiagnosisResult {
  result: string;
  rank?: number;
  diagnosisRank?: number;
  netId?: string;
  cellName?: string;
  neighborFrom?: string;
  neighborTo?: string;
  chain?: string;
  confidencePct?: number;
  confidenceScore?: number;
  diagnosisConfidencePct?: number;
  consistencyRatio?: number;
  consistentPatterns?: number;
  totalFailingPatterns?: number;
  powerInducedRuledOut?: boolean;
  historicalMatchCount?: number;
  faultHypothesis?: string;
  dieLocalXUm?: number;
  dieLocalYUm?: number;
  waferX?: number;
  waferY?: number;
  debugPriority?: string;
  xyAvailable?: boolean;
  pfaTechnique?: string;
  recommendedAction?: string;
}

export interface KpiWorkspace {
  kpiId: ScanDebugKpiId;
  title: string;
  decision: DecisionPanelData;
  summaryCards: { label: string; value: string }[];
  visualizationType:
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
    | "history";
  vizSeries: VizSeries[];
  breakdown: { dimension: string; value: string; share: number }[];
  impact: EngineeringImpactMetric[];
  timeline: TimelineEvent[];
  rawRows: RawEngineeringRow[];
  copilotStarters: string[];
  howToImplement?: string | null;
  diagnosisResults?:
    | ChainBreakDiagnosisResult[]
    | ConstraintViolationDiagnosisResult[]
    | ConstraintReviewRecDiagnosisResult[]
    | CoverageImpactDiagnosisResult[]
    | TimingViolationDiagnosisResult[]
    | TimingDebugRecDiagnosisResult[]
    | WorstSlackDiagnosisResult[]
    | PowerViolationDiagnosisResult[]
    | PowerDebugRecDiagnosisResult[]
    | PeakSwitchingDiagnosisResult[]
    | DefectSuspectDiagnosisResult[]
    | InvestigationRecDiagnosisResult[]
    | DefectLocalizationDiagnosisResult[];
  layout?:
    | "default"
    | "broken_chains_clean"
    | "scan_chain_recs_clean"
    | "scan_chain_confidence_clean"
    | "constraint_violations_clean"
    | "constraint_review_recs_clean"
    | "coverage_impact_clean"
    | "timing_violations_clean"
    | "timing_debug_recs_clean"
    | "worst_slack_clean"
    | "power_violations_clean"
    | "power_debug_recs_clean"
    | "peak_switching_clean"
    | "defect_suspects_clean"
    | "investigation_recs_clean"
    | "defect_localization_clean";
  powerViolationSummary?: {
    count?: number;
    totalPatternsInRun?: number;
    flaggedDespitePass?: number;
    byKind?: Record<string, number>;
    irThresholdMv?: number;
    thermalThresholdC?: number;
    kpiValue?: string;
  };
  powerDebugRecSummary?: {
    count?: number;
    workspaceRows?: number;
  };
  peakSwitchingSummary?: {
    peakIrDropMv?: number;
    avgIrDropMv?: number;
    patternId?: string;
    patternLabel?: string;
    result?: string;
    kpiValue?: string;
    patternCount?: number;
    count?: number;
    deltaVsAvgMv?: number;
  };
  defectSuspectSummary?: {
    count?: number;
    totalCandidates?: number;
    kpiValue?: string;
    result?: string;
    topNetId?: string;
    topConsistency?: string;
    byRootCause?: Record<string, number>;
    topN?: number;
  };
  investigationRecSummary?: {
    count?: number;
    kpiValue?: string;
    result?: string;
    transitionFaultCount?: number;
    irDropMv?: number;
    irThresholdMv?: number;
    powerInducedRuledOut?: boolean;
    ruledOutCount?: number;
    byFaultHypothesis?: Record<string, number>;
    topN?: number;
  };
  defectLocalizationSummary?: {
    count?: number;
    kpiValue?: string;
    averageConfidencePct?: number;
    result?: string;
    topNetId?: string;
    topConfidencePct?: number;
    xyAvailableCount?: number;
    byPriority?: Record<string, number>;
    topN?: number;
  };
}

export interface ScanDebugDashboardData {
  kpis: KpiCardModel[];
  rootCauseDistribution: ChartSlice[];
  recommendationPriority: ChartSlice[];
  recommendationTrend: TrendPoint[];
  aiConfidence: number;
  approvalTrend: TrendPoint[];
  recommendations: RecommendationRow[];
  executiveSummary: ExecutiveSummaryCard[];
  workflow: WorkflowStep[];
}
