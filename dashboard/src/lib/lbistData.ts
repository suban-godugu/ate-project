import { generateGridHeatmap } from "@/lib/heatmapUtils";
import type {
  AIRecommendationRow,
  AffectedLogicRow,
  DebugRecommendationRow,
  DiagnosisReportRow,
  FailureDistribution,
  FailureRecordRow,
  HealthSegment,
  LbistAIDiagnosis,
  LbistFailureRow,
  LbistKPI,
  LogicFailureSummaryRow,
  ModuleFailData,
  RiskCard,
  TrendPoint,
} from "@/types/lbist";

export const overviewKPIs: LbistKPI[] = [
  { id: "total-blocks", title: "Total Logic Blocks", value: "3,842", change: 1.8, trend: "up", sparkline: [3650, 3680, 3720, 3760, 3790, 3815, 3842], icon: "blocks", positiveIsGood: true },
  { id: "coverage", title: "LBIST Coverage", value: "96.2%", change: 1.2, trend: "up", sparkline: [93.8, 94.2, 94.8, 95.2, 95.6, 95.9, 96.2], icon: "target", positiveIsGood: true },
  { id: "passed", title: "Passed Logic Blocks", value: "3,624", change: 1.5, trend: "up", sparkline: [3450, 3480, 3520, 3560, 3590, 3610, 3624], icon: "check-circle", positiveIsGood: true },
  { id: "failed", title: "Failed Logic Blocks", value: "142", change: -8.4, trend: "down", sparkline: [186, 175, 168, 162, 154, 148, 142], icon: "x-circle", positiveIsGood: false },
  { id: "runtime", title: "Average LBIST Runtime", value: "18.6s", change: -2.8, trend: "down", sparkline: [21, 20.5, 20, 19.5, 19, 18.8, 18.6], icon: "timer", positiveIsGood: false },
  { id: "signature-rate", title: "Signature Match Rate", value: "94.8%", change: 2.1, trend: "up", sparkline: [90, 91, 92, 93, 94, 94.5, 94.8], icon: "fingerprint", positiveIsGood: true },
];

export const coverageKPIs: LbistKPI[] = [
  { id: "overall-coverage", title: "Overall Coverage", value: "96.2%", change: 1.2, trend: "up", sparkline: [93.8, 94.2, 94.8, 95.2, 95.6, 95.9, 96.2], icon: "target", positiveIsGood: true },
  { id: "detected-faults", title: "Detected Faults", value: "284", change: 6.4, trend: "up", sparkline: [240, 252, 260, 268, 274, 280, 284], icon: "search-check", positiveIsGood: true },
  { id: "undetected-faults", title: "Undetected Faults", value: "38", change: -12.2, trend: "down", sparkline: [52, 48, 46, 44, 42, 40, 38], icon: "help-circle", positiveIsGood: false },
  { id: "efficiency", title: "Coverage Efficiency", value: "91.4%", change: 2.8, trend: "up", sparkline: [84, 86, 87.5, 89, 90, 91, 91.4], icon: "zap", positiveIsGood: true },
  { id: "compression", title: "Pattern Compression", value: "68.2%", change: 4.6, trend: "up", sparkline: [58, 60, 62, 64, 66, 67, 68.2], icon: "minimize-2", positiveIsGood: true },
  { id: "improvement", title: "Coverage Improvement", value: "+2.4%", change: 2.4, trend: "up", sparkline: [0.4, 0.8, 1.2, 1.6, 2, 2.2, 2.4], icon: "trending-up", positiveIsGood: true },
];

export const failureKPIs: LbistKPI[] = [
  { id: "total-failures", title: "Total Failures", value: "286", change: -5.2, trend: "down", sparkline: [320, 310, 302, 296, 292, 288, 286], icon: "x-circle", positiveIsGood: false },
  { id: "critical-failures", title: "Critical Failures", value: "32", change: -14.8, trend: "down", sparkline: [48, 44, 40, 38, 36, 34, 32], icon: "alert-octagon", positiveIsGood: false },
  { id: "transition-faults", title: "Transition Faults", value: "68", change: -3.8, trend: "down", sparkline: [76, 74, 72, 71, 70, 69, 68], icon: "git-branch", positiveIsGood: false },
  { id: "delay-faults", title: "Delay Faults", value: "42", change: -4.2, trend: "down", sparkline: [48, 47, 46, 45, 44, 43, 42], icon: "clock", positiveIsGood: false },
  { id: "logic-errors", title: "Logic Errors", value: "54", change: -2.1, trend: "down", sparkline: [58, 57, 56, 56, 55, 54, 54], icon: "binary", positiveIsGood: false },
  { id: "unknown-faults", title: "Unknown Faults", value: "18", change: -10.0, trend: "down", sparkline: [24, 22, 21, 20, 19, 18, 18], icon: "help-circle", positiveIsGood: false },
];

export const diagnosisKPIs: LbistKPI[] = [
  { id: "diagnosed", title: "Diagnosed Logic Blocks", value: "2,842", change: 5.8, trend: "up", sparkline: [2540, 2620, 2680, 2740, 2780, 2810, 2842], icon: "search-check", positiveIsGood: true },
  { id: "pending", title: "Pending Diagnosis", value: "48", change: -16.4, trend: "down", sparkline: [72, 68, 62, 58, 54, 50, 48], icon: "clock", positiveIsGood: false },
  { id: "ai-confidence", title: "AI Confidence", value: "90.6%", change: 2.4, trend: "up", sparkline: [84, 86, 87.5, 88.5, 89.5, 90, 90.6], icon: "gauge", positiveIsGood: true },
  { id: "validation", title: "Coverage Validation", value: "93.8%", change: 1.6, trend: "up", sparkline: [90, 91, 91.8, 92.5, 93, 93.5, 93.8], icon: "shield-check", positiveIsGood: true },
  { id: "repair-suggestions", title: "Repair Suggestions", value: "96", change: 14.2, trend: "up", sparkline: [68, 72, 78, 82, 88, 92, 96], icon: "lightbulb", positiveIsGood: true },
  { id: "detection-accuracy", title: "Detection Accuracy", value: "92.4%", change: 1.8, trend: "up", sparkline: [88, 89, 90, 91, 91.5, 92, 92.4], icon: "crosshair", positiveIsGood: true },
];

export const coverageDistribution: HealthSegment[] = [
  { name: "Passed", value: 3624, color: "#22C55E" },
  { name: "Failed", value: 142, color: "#EF4444" },
  { name: "Partial Coverage", value: 58, color: "#EAB308" },
  { name: "Untested", value: 18, color: "#64748B" },
];

export const failureByModule: ModuleFailData[] = [
  { module: "CPU-Core-0", failCount: 22 },
  { module: "GPU-Shader-A", failCount: 18 },
  { module: "NOC-Router-2", failCount: 16 },
  { module: "PCIe-CTRL-1", failCount: 14 },
  { module: "DSP-Accel-0", failCount: 12 },
  { module: "Cache-L2-Bank3", failCount: 11 },
  { module: "IO-Hub-South", failCount: 10 },
  { module: "Security-Block", failCount: 9 },
  { module: "Clock-Tree-East", failCount: 8 },
  { module: "Debug-Wrapper", failCount: 6 },
];

export const recentFailures: LbistFailureRow[] = [
  { sessionId: "LB-20260629-001", logicBlock: "LB-CPU-042", controller: "CTRL-A1", misrSignature: "0xA4F28B1C", expectedSignature: "0xA4F28B1C", coverage: 98.2, status: "Failed", timestamp: "2026-06-29 10:12" },
  { sessionId: "LB-20260629-002", logicBlock: "LB-GPU-118", controller: "CTRL-B2", misrSignature: "0x8B2C104E", expectedSignature: "0x8B2C109A", coverage: 94.6, status: "Critical", timestamp: "2026-06-29 10:08" },
  { sessionId: "LB-20260629-003", logicBlock: "LB-NOC-007", controller: "CTRL-C1", misrSignature: "0x4E891432", expectedSignature: "0x4E891432", coverage: 96.8, status: "Failed", timestamp: "2026-06-29 09:54" },
  { sessionId: "LB-20260629-004", logicBlock: "LB-PCIe-056", controller: "CTRL-A2", misrSignature: "0xC0120048", expectedSignature: "0xC0120048", coverage: 97.4, status: "Warning", timestamp: "2026-06-29 09:42" },
  { sessionId: "LB-20260629-005", logicBlock: "LB-DSP-089", controller: "CTRL-D1", misrSignature: "0x2F8A44AC", expectedSignature: "0x2F8A44B8", coverage: 92.1, status: "Critical", timestamp: "2026-06-29 09:30" },
  { sessionId: "LB-20260629-006", logicBlock: "LB-CACHE-014", controller: "CTRL-B1", misrSignature: "0x6D1028F0", expectedSignature: "0x6D1028F0", coverage: 95.8, status: "Failed", timestamp: "2026-06-29 09:18" },
  { sessionId: "LB-20260629-007", logicBlock: "LB-IO-032", controller: "CTRL-C2", misrSignature: "0x9A3B6C12", expectedSignature: "0x9A3B6C12", coverage: 93.4, status: "Warning", timestamp: "2026-06-29 09:06" },
  { sessionId: "LB-20260629-008", logicBlock: "LB-SEC-201", controller: "CTRL-A3", misrSignature: "0x1104F088", expectedSignature: "0x1104F09C", coverage: 91.2, status: "Failed", timestamp: "2026-06-29 08:58" },
];

export const failureTypeDistribution: FailureDistribution[] = [
  { name: "Transition Fault", value: 28, color: "#7C3AED" },
  { name: "Stuck-at Fault", value: 24, color: "#06B6D4" },
  { name: "Bridging Fault", value: 16, color: "#F97316" },
  { name: "Delay Fault", value: 14, color: "#EAB308" },
  { name: "Logic Fault", value: 12, color: "#22C55E" },
  { name: "Unknown", value: 6, color: "#64748B" },
];

export const aiDiagnosisSummary: LbistAIDiagnosis = {
  likelyRootCause: "MISR mismatch due to transition fault in GPU shader pipeline LB-GPU-118",
  criticalLogicBlocks: 14,
  coverageGap: "3.8% uncovered in NOC-Router-2 cluster",
  diagnosisConfidence: 91,
  estimatedYieldImpact: "-1.6%",
};

export const coverageTrend: TrendPoint[] = [
  { label: "Mon", value: 93.8, value2: 88 }, { label: "Tue", value: 94.2, value2: 89 },
  { label: "Wed", value: 94.8, value2: 90 }, { label: "Thu", value: 95.2, value2: 91 },
  { label: "Fri", value: 95.6, value2: 92 }, { label: "Sat", value: 95.9, value2: 92.5 }, { label: "Sun", value: 96.2, value2: 93 },
];

export const coverageByBlock: TrendPoint[] = [
  { label: "CPU", value: 98 }, { label: "GPU", value: 92 }, { label: "NOC", value: 94 },
  { label: "PCIe", value: 96 }, { label: "DSP", value: 90 }, { label: "Cache", value: 97 },
];

export const patternEfficiency: TrendPoint[] = [
  { label: "Pat-A", value: 92 }, { label: "Pat-B", value: 88 }, { label: "Pat-C", value: 94 },
  { label: "Pat-D", value: 86 }, { label: "Pat-E", value: 90 },
];

export const faultDetectionRate: TrendPoint[] = [
  { label: "Mon", value: 88 }, { label: "Tue", value: 89.5 }, { label: "Wed", value: 90.2 },
  { label: "Thu", value: 91 }, { label: "Fri", value: 91.8 }, { label: "Sat", value: 92 }, { label: "Sun", value: 92.4 },
];

export const failureTrend: TrendPoint[] = [
  { label: "Mon", value: 98, value2: 28 }, { label: "Tue", value: 92, value2: 26 },
  { label: "Wed", value: 88, value2: 24 }, { label: "Thu", value: 84, value2: 22 },
  { label: "Fri", value: 80, value2: 20 }, { label: "Sat", value: 82, value2: 21 }, { label: "Sun", value: 78, value2: 18 },
];

export const failureByBlock: TrendPoint[] = failureByModule.map((m) => ({ label: m.module.replace(/-/g, " "), value: m.failCount }));

export const failureDensity: TrendPoint[] = [
  { label: "Zone A", value: 86 }, { label: "Zone B", value: 62 }, { label: "Zone C", value: 78 },
  { label: "Zone D", value: 54 }, { label: "Zone E", value: 70 }, { label: "Zone F", value: 48 },
];

export const failureRecords: FailureRecordRow[] = recentFailures.map((r, i) => ({
  failureId: `F-LB-${10280 + i}`,
  sessionId: r.sessionId,
  logicBlock: r.logicBlock,
  failType: r.status === "Critical" ? "Transition Fault" : "Logic Fault",
  severity: r.status === "Critical" ? "Critical" : r.status === "Warning" ? "Warning" : "Recovered",
  timestamp: r.timestamp,
}));

export const logicFailureSummary: LogicFailureSummaryRow[] = [
  { logicBlock: "LB-GPU-118", module: "GPU-Shader-A", failCount: 18, coverage: 92.1, status: "Escalated" },
  { logicBlock: "LB-CPU-042", module: "CPU-Core-0", failCount: 14, coverage: 96.4, status: "Active" },
  { logicBlock: "LB-NOC-007", module: "NOC-Router-2", failCount: 12, coverage: 94.8, status: "Active" },
  { logicBlock: "LB-DSP-089", module: "DSP-Accel-0", failCount: 10, coverage: 91.2, status: "Resolved" },
];

export const diagnosisTimeline: TrendPoint[] = [
  { label: "Week 1", value: 720, value2: 52 }, { label: "Week 2", value: 820, value2: 48 },
  { label: "Week 3", value: 920, value2: 42 }, { label: "Week 4", value: 1020, value2: 36 },
  { label: "Week 5", value: 1120, value2: 32 }, { label: "Week 6", value: 1200, value2: 28 },
];

export const failureCorrelation: TrendPoint[] = [
  { label: "T+0", value: 10 }, { label: "T+1", value: 22 }, { label: "T+2", value: 38 },
  { label: "T+3", value: 48 }, { label: "T+4", value: 42 }, { label: "T+5", value: 28 }, { label: "T+6", value: 14 },
];

export const coverageCorrelation: TrendPoint[] = [
  { label: "Mon", value: 84 }, { label: "Tue", value: 86 }, { label: "Wed", value: 88 },
  { label: "Thu", value: 89.5 }, { label: "Fri", value: 90.6 }, { label: "Sat", value: 90.4 }, { label: "Sun", value: 90.6 },
];

export const diagnosisReports: DiagnosisReportRow[] = [
  { logicBlock: "LB-GPU-118", status: "Diagnosed", rootCause: "Transition fault in shader ALU", confidence: 91, repairSuggestion: "Increase hold margin on path 118-A" },
  { logicBlock: "LB-CPU-042", status: "Partial", rootCause: "MISR compression mismatch", confidence: 78, repairSuggestion: "Re-run with extended pattern set" },
  { logicBlock: "LB-NOC-007", status: "Diagnosed", rootCause: "Coverage gap in router segment", confidence: 94, repairSuggestion: "Add targeted LBIST pattern for NOC-007" },
  { logicBlock: "LB-SEC-201", status: "Unknown", rootCause: "Pending analysis", confidence: 42, repairSuggestion: "Run extended diagnosis session" },
];

export const affectedLogicBlocks: AffectedLogicRow[] = [
  { logicBlock: "LB-GPU-118", module: "GPU-Shader-A", failProbability: 0.92, coverage: 92.1 },
  { logicBlock: "LB-CPU-042", module: "CPU-Core-0", failProbability: 0.86, coverage: 96.4 },
  { logicBlock: "LB-NOC-007", module: "NOC-Router-2", failProbability: 0.88, coverage: 94.8 },
  { logicBlock: "LB-DSP-089", module: "DSP-Accel-0", failProbability: 0.78, coverage: 91.2 },
];

export const debugRecommendations: DebugRecommendationRow[] = [
  { id: "DBG-001", logicBlock: "LB-GPU-118", recommendation: "Inspect transition paths in shader segment 118", priority: 1 },
  { id: "DBG-002", logicBlock: "LB-NOC-007", recommendation: "Validate coverage for router cluster 007", priority: 2 },
  { id: "DBG-003", logicBlock: "LB-CPU-042", recommendation: "Review MISR signature compression chain", priority: 3 },
  { id: "DBG-004", logicBlock: "LB-DSP-089", recommendation: "Check delay fault on DSP datapath", priority: 4 },
];

export const aiRecommendations: AIRecommendationRow[] = [
  { id: "AI-LB-001", logicBlock: "LB-GPU-118", recommendation: "Add transition margin pattern for shader ALU", priority: "High", confidence: 91, expectedBenefit: "+1.2% yield" },
  { id: "AI-LB-002", logicBlock: "LB-NOC-007", recommendation: "Extend LBIST coverage for NOC cluster", priority: "High", confidence: 88, expectedBenefit: "+0.8% coverage" },
  { id: "AI-LB-003", logicBlock: "LB-CPU-042", recommendation: "Optimize MISR compression sequence", priority: "Medium", confidence: 82, expectedBenefit: "-4.2s runtime" },
  { id: "AI-LB-004", logicBlock: "LB-DSP-089", recommendation: "Apply delay fault screening pattern", priority: "Medium", confidence: 76, expectedBenefit: "+0.5% yield" },
];

export const riskCards: RiskCard[] = [
  { title: "Coverage Improvement", value: "12", subtitle: "Suggested pattern additions", icon: "target" },
  { title: "Pattern Optimization", value: "8", subtitle: "Compressible patterns", icon: "zap" },
  { title: "Logic Repair Candidates", value: "14", subtitle: "Blocks needing repair", icon: "wrench" },
  { title: "Risk Score", value: "5.8/10", subtitle: "Aggregate logic risk", icon: "gauge" },
  { title: "Yield Improvement", value: "+3.6%", subtitle: "If all actions applied", icon: "trending-up" },
  { title: "Test Time Reduction", value: "-12.4s", subtitle: "Per lot projected savings", icon: "timer" },
  { title: "Cost Savings", value: "$142K", subtitle: "Monthly projected savings", icon: "dollar" },
];


export function generateCoverageHeatmap(rows = 14, cols = 22): { value: number; row: number; col: number }[] {
  return generateGridHeatmap(rows, cols, 0.35, 0.65);
}

export const connectivityNodes = {
  nodes: [
    { id: "LB-GPU-118", label: "LB-GPU-118", status: "failed" },
    { id: "LB-CPU-042", label: "LB-CPU-042", status: "warning" },
    { id: "LB-NOC-007", label: "LB-NOC-007", status: "failed" },
    { id: "LB-PCIe-056", label: "LB-PCIe-056", status: "healthy" },
    { id: "LB-DSP-089", label: "LB-DSP-089", status: "warning" },
  ],
  edges: [
    { from: "LB-GPU-118", to: "LB-CPU-042" },
    { from: "LB-CPU-042", to: "LB-NOC-007" },
    { from: "LB-NOC-007", to: "LB-PCIe-056" },
    { from: "LB-PCIe-056", to: "LB-DSP-089" },
  ],
};
