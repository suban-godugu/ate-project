export type LbistTab =
  | "overview"
  | "coverage-analysis"
  | "failure-analysis"
  | "diagnosis"
  | "ai-recommendation";

export interface LbistKPI {
  id: string;
  title: string;
  value: string;
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

export interface ModuleFailData {
  module: string;
  failCount: number;
}

export interface LbistFailureRow {
  sessionId: string;
  logicBlock: string;
  controller: string;
  misrSignature: string;
  expectedSignature: string;
  coverage: number;
  status: "Failed" | "Warning" | "Critical";
  timestamp: string;
}

export interface FailureDistribution {
  name: string;
  value: number;
  color: string;
}

export interface LbistAIDiagnosis {
  likelyRootCause: string;
  criticalLogicBlocks: number;
  coverageGap: string;
  diagnosisConfidence: number;
  estimatedYieldImpact: string;
}

export interface TrendPoint {
  label: string;
  value: number;
  value2?: number;
}

export interface FailureRecordRow {
  failureId: string;
  sessionId: string;
  logicBlock: string;
  failType: string;
  severity: "Critical" | "Warning" | "Recovered";
  timestamp: string;
}

export interface LogicFailureSummaryRow {
  logicBlock: string;
  module: string;
  failCount: number;
  coverage: number;
  status: "Active" | "Resolved" | "Escalated";
}

export interface DiagnosisReportRow {
  logicBlock: string;
  status: "Diagnosed" | "Unknown" | "Partial";
  rootCause: string;
  confidence: number;
  repairSuggestion: string;
}

export interface AffectedLogicRow {
  logicBlock: string;
  module: string;
  failProbability: number;
  coverage: number;
}

export interface DebugRecommendationRow {
  id: string;
  logicBlock: string;
  recommendation: string;
  priority: number;
}

export interface AIRecommendationRow {
  id: string;
  logicBlock: string;
  recommendation: string;
  priority: "High" | "Medium" | "Low";
  confidence: number;
  expectedBenefit: string;
}

export interface RiskCard {
  title: string;
  value: string;
  subtitle: string;
  icon: string;
}
