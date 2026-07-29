import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";

export type ScanChainTab =
  | "overview"
  | "pattern-analysis"
  | "failure-analysis"
  | "scan-diagnosis";

export interface ScanKPI {
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

export interface HealthSegment {
  name: string;
  value: number;
  color: string;
}

export interface ChipFailData {
  chip: string;
  failCount: number;
}

export interface FailingChainRow {
  chainId: string;
  patternId: string;
  chip: string;
  failCycle: number;
  failType: string;
  rootCause: string;
  diagnosisStatus: "Pending" | "In Progress" | "Complete" | "Escalated";
}

export interface FailureDistribution {
  name: string;
  value: number;
  color: string;
}

export interface AIDiagnosisSummary {
  detectedRootCause: string;
  criticalChains: number;
  recommendedDebugArea: string;
  estimatedRepairSuccess: number;
  confidenceScore: number;
}

export interface TrendPoint {
  label: string;
  value: number;
  value2?: number;
}

export interface PatternSummaryRow {
  patternId: string;
  chainCount: number;
  coverage: number;
  runtime: number;
  efficiency: number;
  status: "Active" | "Inactive" | "Deprecated";
}

export interface PatternRecommendationRow {
  patternId: string;
  issue: string;
  recommendation: string;
  priority: "High" | "Medium" | "Low";
}

export type PatternStatusVariant = "success" | "warning" | "danger" | "neutral" | "info";

export interface PatternAnalysisKPI {
  id: string;
  title: string;
  value: string;
  subtitle?: string;
  status: string;
  statusVariant?: PatternStatusVariant;
  description: string;
  change: number;
  trend: "up" | "down";
  sparkline: number[];
  icon: string;
  positiveIsGood?: boolean;
}

export interface PatternAnalysisRow {
  patternId: string;
  patternName: string;
  fileType: string;
  coverage: number;
  compressionRatio: number;
  vectors: number;
  cluster: string;
  similarityScore: number;
  redundancy: string;
  qualityScore: number;
  status: "Active" | "Review" | "Redundant" | "Deprecated";
  recommendation: string;
}

export interface PatternScatterPoint {
  x: number;
  y: number;
  cluster: string;
  patternId: string;
}

export interface PatternAISummary {
  patternsToRemove: number;
  patternsToMerge: number;
  coverageImprovement: string;
  compressionImprovement: string;
  missingMetadata: number;
  duplicatePatterns: number;
  expectedRuntimeReduction: string;
  expectedYieldImprovement: string;
}

export interface FailureRecordRow {
  failureId: string;
  chainId: string;
  chip: string;
  failType: string;
  severity: "Critical" | "Warning" | "Recovered";
  timestamp: string;
}

export type FailureKPIFocus = "wafer-heatmap" | "die-heatmap";

export interface FailureAnalysisKPI {
  id: string;
  title: string;
  value: string;
  subtitle?: string;
  status: string;
  statusVariant?: PatternStatusVariant;
  description: string;
  change: number;
  trend: "up" | "down";
  sparkline: number[];
  icon: string;
  positiveIsGood?: boolean;
  focusTarget?: FailureKPIFocus;
}

export interface FailureAnalysisRow {
  failureId: string;
  patternId: string;
  lotId: string;
  waferId: string;
  dieId: string;
  faultCategory: string;
  rootCause: string;
  confidence: number;
  severity: "Critical" | "High" | "Medium" | "Low";
  status: "Open" | "Investigating" | "Resolved" | "Escalated";
  recommendation: string;
  timestamp: string;
}

export interface FailureAISummary {
  highestFailureLot: string;
  highestFailureWafer: string;
  criticalFaultCategory: string;
  mostAffectedPattern: string;
  mostFrequentRootCause: string;
  estimatedYieldLoss: string;
  estimatedCostImpact: string;
  recommendedEngineeringAction: string;
}

export interface RootCauseTreeNode {
  id: string;
  cause: string;
  confidence: number;
  affectedPatterns: number;
  children?: RootCauseTreeNode[];
}

export interface LotFailData {
  lot: string;
  failCount: number;
}

export interface RootCauseRow {
  cause: string;
  count: number;
  percentage: number;
  trend: number;
}

export interface AIRecommendationRow {
  id: string;
  chainId: string;
  recommendation: string;
  confidence: number;
  impact: "High" | "Medium" | "Low";
}

export interface DiagnosisReportRow {
  chainId: string;
  status: "Diagnosed" | "Unknown" | "Partial";
  rootCause: string;
  confidence: number;
  repairSuggestion: string;
}

export interface SuspectedCellRow {
  cellId: string;
  chainId: string;
  cellType: string;
  failProbability: number;
  location: string;
}

export interface DebugPointRow {
  pointId: string;
  chainId: string;
  region: string;
  priority: number;
  description: string;
}

export interface RepairPriorityRow {
  chainId: string;
  priority: number;
  failType: string;
  estimatedFixTime: string;
  successRate: number;
}

export interface ScanDiagnosisKPI {
  id: string;
  title: string;
  value: string;
  subtitle?: string;
  status: string;
  statusVariant?: PatternStatusVariant;
  description: string;
  change: number;
  trend: "up" | "down";
  sparkline: number[];
  icon: string;
  positiveIsGood?: boolean;
}

export interface ScanDiagnosisKPISection {
  title: string;
  kpis: ScanDiagnosisKPI[];
}

export interface ChainFailRankingData {
  chain: string;
  failCount: number;
}

export interface ScanDiagnosisRecommendationRow {
  diagnosisId: string;
  scanChain: string;
  failingCell: string;
  rootCause: string;
  confidence: number;
  priority: "Critical" | "High" | "Medium" | "Low";
  affectedLot: string;
  affectedWafer: string;
  engineer: string;
  status: "Pending" | "Approved" | "In Review" | "Validated";
}

export interface ScanDiagnosisExecutiveSummary {
  title: string;
  subtitle: string;
  metrics: { label: string; value: string }[];
}

export interface FailureCorrelationMatrix {
  rowLabels: string[];
  colLabels: string[];
  grid: number[][];
}

export interface TopologyGraphNode {
  id: string;
  label: string;
  status: "broken" | "failing-cell" | "debug" | "healthy" | "warning";
}

export interface TopologyGraphEdge {
  from: string;
  to: string;
  broken?: boolean;
}

export interface TableColumn<T> {
  key: keyof T;
  label: string;
  render?: (row: T) => ReactNode;
}

export interface KPIIconMap {
  [key: string]: LucideIcon;
}

export interface OverviewExecutiveInsights {
  summary: string;
  mostCriticalChain: string;
  mostCriticalPattern: string;
  highestFailureLot: string;
  highestFailureWafer: string;
  mostCommonRootCause: string;
  confidence: string;
  estimatedSaving: string;
  priorityRecommendation: string;
}

export interface OverviewTrendChart {
  id: string;
  title: string;
  data: TrendPoint[];
  lines?: { key: keyof TrendPoint; color: string; name: string }[];
}

export interface OverviewRecommendationPreviewRow {
  id: string;
  recommendation: string;
  confidence: number;
  expectedSaving: string;
  priority: "Critical" | "High" | "Medium" | "Low";
  status: string;
}

export interface OverviewAlertPreviewRow {
  id: string;
  title: string;
  severity: "Critical" | "High" | "Warning";
  status: string;
}

export interface OverviewUploadActivityRow {
  id: string;
  fileName: string;
  patternsParsed: string;
  chainsParsed: string;
  failuresFound: string;
  parser: string;
  uploadTime: string;
  status: string;
}
