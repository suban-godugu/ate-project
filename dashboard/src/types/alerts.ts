export type AlertTab =
  | "overview"
  | "scan-chain"
  | "mbist"
  | "lbist"
  | "wafer"
  | "cost"
  | "ai-recommendation";

export type Severity = "Critical" | "High" | "Medium" | "Low";

export type AlertModule =
  | "Scan Chain"
  | "MBIST"
  | "LBIST"
  | "Wafer"
  | "Cost"
  | "AI Recommendation";

export type AlertStatus = "Open" | "Investigating" | "Resolved" | "Closed" | "Pending";

export interface AlertKPI {
  id: string;
  title: string;
  value: string;
  change: number;
  trend: "up" | "down";
  sparkline: number[];
  icon: string;
  positiveIsGood?: boolean;
}

export interface AlertSegment {
  name: string;
  value: number;
  color: string;
}

export interface TrendPoint {
  label: string;
  value: number;
  value2?: number;
}

export interface RecentAlertRow {
  id: string;
  sourceModule: AlertModule;
  lotId: string;
  waferId: string;
  severity: Severity;
  description: string;
  status: AlertStatus;
  assignedEngineer: string;
  createdTime: string;
}

export interface CriticalAlertSummary {
  mostCriticalIssue: string;
  affectedProduct: string;
  affectedTester: string;
  affectedLot: string;
  estimatedYieldImpact: string;
  estimatedCostImpact: string;
  recommendedAction: string;
}

export interface ScanChainAlertRow {
  id: string;
  chainId: string;
  pattern: string;
  severity: Severity;
  recommendation: string;
  status: AlertStatus;
}

export interface MbistAlertRow {
  id: string;
  memory: string;
  bank: string;
  severity: Severity;
  recommendation: string;
}

export interface LbistAlertRow {
  id: string;
  logicBlock: string;
  severity: Severity;
  recommendation: string;
}

export interface WaferAlertRow {
  id: string;
  lot: string;
  wafer: string;
  severity: Severity;
  recommendation: string;
}

export interface CostAlertRow {
  id: string;
  module: AlertModule;
  currentCost: string;
  threshold: string;
  recommendation: string;
}

export interface AIRecommendationAlertRow {
  id: string;
  sourceModule: AlertModule;
  priority: Severity;
  confidence: number;
  status: AlertStatus;
  engineer: string;
}

export interface ExecutiveAlertSummary {
  criticalAlerts: string;
  openAlerts: string;
  resolvedToday: string;
  averageResolutionTime: string;
  estimatedYieldLoss: string;
  estimatedCostImpact: string;
  topPriorityModule: string;
}

export const alertWorkflowSteps = [
  "Issue Detected",
  "Alert Generated",
  "AI Root Cause Analysis",
  "Engineer Assigned",
  "Investigation",
  "Resolved",
  "Closed",
];
