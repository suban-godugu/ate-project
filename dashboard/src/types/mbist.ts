export type MbistTab =
  | "overview"
  | "memory-health"
  | "failure-analysis"
  | "diagnosis"
  | "ai-recommendation";

export interface MbistKPI {
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

export interface BankFailData {
  bank: string;
  failCount: number;
}

export interface MbistFailureRow {
  memoryId: string;
  memoryType: string;
  bank: string;
  address: string;
  failureType: string;
  status: "Failed" | "Warning" | "Critical";
  repairStatus: "Pending" | "In Progress" | "Repaired" | "Not Repairable";
  timestamp: string;
}

export interface FailureDistribution {
  name: string;
  value: number;
  color: string;
}

export interface MbistAIDiagnosis {
  likelyRootCause: string;
  repairableMemories: number;
  nonRepairableMemories: number;
  repairEfficiency: number;
  diagnosisConfidence: number;
}

export interface TrendPoint {
  label: string;
  value: number;
  value2?: number;
}

export interface FailureRecordRow {
  failureId: string;
  memoryId: string;
  memoryType: string;
  bank: string;
  failType: string;
  severity: "Critical" | "Warning" | "Recovered";
  timestamp: string;
}

export interface DiagnosisReportRow {
  memoryId: string;
  status: "Diagnosed" | "Unknown" | "Partial";
  rootCause: string;
  confidence: number;
  repairSuggestion: string;
}

export interface FailAddressRow {
  address: string;
  memoryId: string;
  bank: string;
  failType: string;
  probability: number;
}

export interface RepairRecommendationRow {
  memoryId: string;
  recommendation: string;
  priority: number;
  successRate: number;
}

export interface AIRecommendationRow {
  id: string;
  memoryInstance: string;
  recommendation: string;
  priority: "High" | "Medium" | "Low";
  confidence: number;
  expectedYieldGain: string;
}

export interface RiskCard {
  title: string;
  value: string;
  subtitle: string;
  icon: string;
}
