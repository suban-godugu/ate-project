export type RecommendationTab =
  | "overview"
  | "scan-chain"
  | "mbist"
  | "lbist"
  | "wafer";

export type RecommendationAgentTab =
  | "pattern-agent"
  | "scan-debug-agent"
  | "test-optimization-agent";

export type Priority = "Critical" | "High" | "Medium" | "Low";

export interface RecommendationRlFields {
  feedbackCount?: number;
  rewardScore?: number;
  approvalRate?: number;
  rejectionRate?: number;
  applicationRate?: number;
  confidenceChange?: number | null;
}

export interface RecKPI {
  id: string;
  title: string;
  value: string;
  change: number;
  trend: "up" | "down";
  sparkline: number[];
  icon: string;
  positiveIsGood?: boolean;
}

export interface CenterKPI extends RecKPI {
  subtitle?: string;
  status?: string;
  statusVariant?: "success" | "warning" | "info" | "neutral" | "danger";
  description: string;
}

export interface AgentMeta {
  title: string;
  responsibilities: string[];
  inputs: string[];
  outputs: string[];
}

export interface PatternRecRow extends RecommendationRlFields {
  recommendationId: string;
  patternId: string;
  recommendation: string;
  priority: Priority;
  confidence: number;
  coverageGain: string;
  powerSaving: string;
  status: string;
}

export interface ScanDebugRecRow extends RecommendationRlFields {
  recommendationId: string;
  category: string;
  scanChain: string;
  rootCause: string;
  recommendation: string;
  priority: Priority;
  confidence: number;
  engineer: string;
  status: string;
  expectedImpact: string;
}

export interface TestOptRecRow extends RecommendationRlFields {
  recommendationId: string;
  optimizationType: string;
  currentValue: string;
  optimizedValue: string;
  estimatedBenefit: string;
  priority: Priority;
  confidence: number;
  status: string;
  assignedEngineer: string;
}

export interface KPISection {
  title: string;
  kpis: CenterKPI[];
}

export interface AgentSummary {
  title: string;
  subtitle: string;
  metrics: { label: string; value: string }[];
}

export interface EnterpriseExecutiveSummary {
  patternsRemoved: number;
  coverageGain: string;
  powerSaving: string;
  yieldImprovement: string;
  testTimeReduction: string;
  costReduction: string;
  roi: string;
  aiConfidence: string;
}

export interface HealthSegment {
  name: string;
  value: number;
  color: string;
}

export interface TrendPoint {
  label: string;
  value: number;
  value2?: number;
}

export interface UnifiedRecommendationRow extends RecommendationRlFields {
  id: string;
  sourceModule: "Scan Chain" | "MBIST" | "LBIST" | "Wafer";
  category: string;
  priority: Priority;
  confidence: number;
  estimatedImpact: string;
  status: "Pending" | "In Review" | "Approved" | "Implemented";
  assignedEngineer: string;
}

export interface AIExecutiveSummary {
  topProblems: string[];
  overallRiskScore: string;
  expectedYieldGain: string;
  expectedCostReduction: string;
  expectedTestTimeReduction: string;
}

export interface ScanChainRecRow {
  id: string;
  scanChain: string;
  pattern: string;
  recommendation: string;
  priority: Priority;
  confidence: number;
  expectedResult: string;
}

export interface MbistRecRow {
  id: string;
  memory: string;
  bank: string;
  recommendation: string;
  priority: Priority;
  confidence: number;
  expectedYield: string;
}

export interface LbistRecRow {
  id: string;
  logicBlock: string;
  recommendation: string;
  priority: Priority;
  confidence: number;
  coverageGain: string;
}

export interface WaferRecRow {
  id: string;
  lotId: string;
  waferId: string;
  recommendation: string;
  priority: Priority;
  confidence: number;
  expectedYield: string;
}

export interface BottomAISummary {
  estimatedSavings: string;
  yieldImprovement: string;
  testTimeReduction: string;
  memoryRepairSuccess: string;
  logicCoverageIncrease: string;
  patternReduction: string;
  waferYieldIncrease: string;
  totalRoi: string;
}

export interface WorkflowStep {
  id: string;
  label: string;
}

export const recommendationCategories = [
  "Pattern Optimization",
  "Scan Compression",
  "Repair Suggestion",
  "Memory Redundancy",
  "Logic Optimization",
  "Wafer Retest",
  "Bin Optimization",
  "Test Time Reduction",
  "Cost Reduction",
  "Yield Improvement",
];
