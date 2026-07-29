import { generateGridHeatmap } from "@/lib/heatmapUtils";
import type {
  AIExecutiveSummary,
  AgentMeta,
  AgentSummary,
  KPISection,
  BottomAISummary,
  CenterKPI,
  EnterpriseExecutiveSummary,
  HealthSegment,
  LbistRecRow,
  MbistRecRow,
  PatternRecRow,
  RecKPI,
  ScanChainRecRow,
  ScanDebugRecRow,
  TestOptRecRow,
  TrendPoint,
  UnifiedRecommendationRow,
  WaferRecRow,
} from "@/types/recommendation";

export const overviewKPIs: RecKPI[] = [
  { id: "total", title: "Total Recommendations", value: "186", change: 12.4, trend: "up", sparkline: [142, 152, 158, 165, 172, 180, 186], icon: "sparkles", positiveIsGood: true },
  { id: "critical", title: "Critical Recommendations", value: "24", change: -8.2, trend: "down", sparkline: [32, 30, 28, 27, 26, 25, 24], icon: "alert-octagon", positiveIsGood: false },
  { id: "high", title: "High Priority", value: "48", change: 4.8, trend: "up", sparkline: [38, 40, 42, 44, 45, 47, 48], icon: "alert-triangle", positiveIsGood: true },
  { id: "medium", title: "Medium Priority", value: "72", change: 6.2, trend: "up", sparkline: [58, 60, 62, 65, 68, 70, 72], icon: "minus-circle", positiveIsGood: true },
  { id: "yield", title: "Estimated Yield Improvement", value: "+5.8%", change: 1.4, trend: "up", sparkline: [3.2, 3.8, 4.2, 4.8, 5.2, 5.5, 5.8], icon: "trending-up", positiveIsGood: true },
  { id: "cost", title: "Estimated Cost Savings", value: "$428K", change: 8.6, trend: "up", sparkline: [320, 340, 360, 380, 400, 415, 428], icon: "dollar", positiveIsGood: true },
];

export const scanChainKPIs: RecKPI[] = [
  { id: "total", title: "Total Scan Recommendations", value: "52", change: 8.4, trend: "up", sparkline: [38, 42, 44, 46, 48, 50, 52], icon: "link", positiveIsGood: true },
  { id: "critical", title: "Critical Scan Chains", value: "12", change: -10.2, trend: "down", sparkline: [18, 16, 15, 14, 13, 12, 12], icon: "alert-octagon", positiveIsGood: false },
  { id: "compression", title: "Compression Optimization", value: "18", change: 14.2, trend: "up", sparkline: [10, 12, 13, 14, 15, 17, 18], icon: "minimize-2", positiveIsGood: true },
  { id: "diagnosis", title: "Diagnosis Accuracy", value: "92.4%", change: 2.1, trend: "up", sparkline: [88, 89, 90, 91, 91.5, 92, 92.4], icon: "crosshair", positiveIsGood: true },
  { id: "coverage", title: "Coverage Improvement", value: "+2.8%", change: 2.8, trend: "up", sparkline: [0.8, 1.2, 1.6, 2, 2.2, 2.5, 2.8], icon: "target", positiveIsGood: true },
  { id: "yield", title: "Expected Yield Gain", value: "+1.6%", change: 0.8, trend: "up", sparkline: [0.6, 0.8, 1, 1.2, 1.3, 1.5, 1.6], icon: "trending-up", positiveIsGood: true },
];

export const mbistKPIs: RecKPI[] = [
  { id: "total", title: "Memory Recommendations", value: "44", change: 6.8, trend: "up", sparkline: [32, 34, 36, 38, 40, 42, 44], icon: "memory", positiveIsGood: true },
  { id: "repair", title: "Repair Candidates", value: "18", change: -4.2, trend: "down", sparkline: [24, 22, 21, 20, 19, 18, 18], icon: "wrench", positiveIsGood: false },
  { id: "health", title: "Memory Health", value: "94.2%", change: 1.2, trend: "up", sparkline: [91, 92, 92.5, 93, 93.5, 94, 94.2], icon: "heart", positiveIsGood: true },
  { id: "repair-success", title: "Repair Success", value: "82.6%", change: 4.1, trend: "up", sparkline: [74, 76, 78, 79, 80, 81.5, 82.6], icon: "check-circle", positiveIsGood: true },
  { id: "coverage", title: "Coverage", value: "97.4%", change: 0.9, trend: "up", sparkline: [95, 95.5, 96, 96.5, 97, 97.2, 97.4], icon: "shield", positiveIsGood: true },
  { id: "runtime", title: "Runtime Improvement", value: "-6.2s", change: -6.2, trend: "down", sparkline: [-2, -3, -3.5, -4.5, -5, -5.8, -6.2], icon: "timer", positiveIsGood: false },
];

export const lbistKPIs: RecKPI[] = [
  { id: "total", title: "Logic Recommendations", value: "38", change: 9.2, trend: "up", sparkline: [28, 30, 32, 33, 35, 36, 38], icon: "binary", positiveIsGood: true },
  { id: "coverage", title: "Coverage Improvement", value: "+3.2%", change: 3.2, trend: "up", sparkline: [1, 1.5, 2, 2.4, 2.8, 3, 3.2], icon: "target", positiveIsGood: true },
  { id: "repair", title: "Logic Repair", value: "14", change: 5.4, trend: "up", sparkline: [10, 11, 11.5, 12, 13, 13.5, 14], icon: "wrench", positiveIsGood: true },
  { id: "signature", title: "Signature Accuracy", value: "94.8%", change: 2.1, trend: "up", sparkline: [90, 91, 92, 93, 94, 94.5, 94.8], icon: "fingerprint", positiveIsGood: true },
  { id: "health", title: "Logic Health", value: "93.6%", change: 1.8, trend: "up", sparkline: [89, 90, 91, 92, 92.5, 93, 93.6], icon: "activity", positiveIsGood: true },
  { id: "runtime", title: "Runtime Reduction", value: "-4.8s", change: -4.8, trend: "down", sparkline: [-1.5, -2, -2.8, -3.2, -4, -4.5, -4.8], icon: "timer", positiveIsGood: false },
];

export const waferKPIs: RecKPI[] = [
  { id: "total", title: "Wafer Recommendations", value: "52", change: 7.4, trend: "up", sparkline: [38, 42, 44, 46, 48, 50, 52], icon: "microscope", positiveIsGood: true },
  { id: "critical", title: "Critical Wafers", value: "8", change: -12.5, trend: "down", sparkline: [14, 12, 11, 10, 9, 8, 8], icon: "alert-octagon", positiveIsGood: false },
  { id: "yield", title: "Yield Improvement", value: "+2.4%", change: 1.2, trend: "up", sparkline: [0.8, 1, 1.2, 1.6, 1.8, 2.1, 2.4], icon: "trending-up", positiveIsGood: true },
  { id: "defect", title: "Defect Density", value: "-18%", change: -18, trend: "down", sparkline: [-8, -10, -12, -14, -15, -16, -18], icon: "scan", positiveIsGood: false },
  { id: "hotspot", title: "Hotspot Detection", value: "16", change: 4.2, trend: "up", sparkline: [10, 11, 12, 13, 14, 15, 16], icon: "flame", positiveIsGood: true },
  { id: "confidence", title: "AI Confidence", value: "91.2%", change: 2.4, trend: "up", sparkline: [86, 87.5, 88.5, 89.5, 90, 90.8, 91.2], icon: "brain", positiveIsGood: true },
];

export const sourceDistribution: HealthSegment[] = [
  { name: "Scan Chain", value: 52, color: "#7C3AED" },
  { name: "MBIST", value: 44, color: "#06B6D4" },
  { name: "LBIST", value: 38, color: "#F97316" },
  { name: "Wafer", value: 52, color: "#22C55E" },
];

export const priorityDistribution: TrendPoint[] = [
  { label: "Critical", value: 24 },
  { label: "High", value: 48 },
  { label: "Medium", value: 72 },
  { label: "Low", value: 42 },
];

export const recommendationTrend: TrendPoint[] = [
  { label: "Day 1", value: 142 }, { label: "Day 5", value: 148 }, { label: "Day 10", value: 155 },
  { label: "Day 15", value: 162 }, { label: "Day 20", value: 172 }, { label: "Day 25", value: 178 }, { label: "Day 30", value: 186 },
];

export const unifiedRecommendations: UnifiedRecommendationRow[] = [
  { id: "REC-001", sourceModule: "Scan Chain", category: "Pattern Optimization", priority: "Critical", confidence: 94, estimatedImpact: "+1.2% yield", status: "In Review", assignedEngineer: "Alex J." },
  { id: "REC-002", sourceModule: "MBIST", category: "Memory Repair", priority: "High", confidence: 91, estimatedImpact: "$42K savings", status: "Approved", assignedEngineer: "Sarah M." },
  { id: "REC-003", sourceModule: "LBIST", category: "Logic Optimization", priority: "High", confidence: 88, estimatedImpact: "+0.8% coverage", status: "Pending", assignedEngineer: "David K." },
  { id: "REC-004", sourceModule: "Wafer", category: "Yield Improvement", priority: "Critical", confidence: 92, estimatedImpact: "+2.1% yield", status: "In Review", assignedEngineer: "Alex J." },
  { id: "REC-005", sourceModule: "Scan Chain", category: "Scan Compression", priority: "Medium", confidence: 86, estimatedImpact: "-8.4s test time", status: "Implemented", assignedEngineer: "Priya R." },
  { id: "REC-006", sourceModule: "MBIST", category: "Memory Redundancy", priority: "Medium", confidence: 84, estimatedImpact: "+0.6% yield", status: "Pending", assignedEngineer: "Sarah M." },
  { id: "REC-007", sourceModule: "Wafer", category: "Wafer Retest", priority: "Low", confidence: 78, estimatedImpact: "+0.4% yield", status: "Approved", assignedEngineer: "David K." },
  { id: "REC-008", sourceModule: "LBIST", category: "Coverage Enhancement", priority: "High", confidence: 89, estimatedImpact: "+1.4% coverage", status: "In Review", assignedEngineer: "Priya R." },
];

export const aiExecutiveSummary: AIExecutiveSummary = {
  topProblems: [
    "Critical scan chain failures in Core-CPU-0 cluster",
    "Memory repair backlog in SRAM Bank-0",
    "LBIST coverage gap in GPU shader pipeline",
    "Wafer yield hotspot in Lot W-2847 edge dies",
  ],
  overallRiskScore: "6.4 / 10",
  expectedYieldGain: "+5.8%",
  expectedCostReduction: "$428K / month",
  expectedTestTimeReduction: "-18.6s / lot",
};

export const scanChainRecommendations: ScanChainRecRow[] = [
  { id: "SC-REC-001", scanChain: "SC-004821", pattern: "PAT-STUCK-042", recommendation: "Compress pattern segments 3-5", priority: "Critical", confidence: 94, expectedResult: "-6.2s runtime" },
  { id: "SC-REC-002", scanChain: "SC-003156", pattern: "PAT-TRANS-118", recommendation: "Add hold-time margin pattern", priority: "High", confidence: 88, expectedResult: "+1.2% yield" },
  { id: "SC-REC-003", scanChain: "SC-007892", pattern: "PAT-BRIDGE-007", recommendation: "Replace with PAT-STUCK-089", priority: "High", confidence: 91, expectedResult: "$18K savings" },
  { id: "SC-REC-004", scanChain: "SC-002441", pattern: "PAT-TIMING-056", recommendation: "Optimize scan ordering", priority: "Medium", confidence: 82, expectedResult: "-3.4s runtime" },
];

export const mbistRecommendations: MbistRecRow[] = [
  { id: "MB-REC-001", memory: "MEM-004821", bank: "Bank-0", recommendation: "Repair address decoder segment", priority: "Critical", confidence: 91, expectedYield: "+0.8%" },
  { id: "MB-REC-002", memory: "MEM-007892", bank: "Bank-1", recommendation: "FIB bit-line isolation", priority: "High", confidence: 88, expectedYield: "+0.6%" },
  { id: "MB-REC-003", memory: "MEM-003156", bank: "Bank-2", recommendation: "Allocate spare row redundancy", priority: "High", confidence: 86, expectedYield: "+0.5%" },
  { id: "MB-REC-004", memory: "MEM-002441", bank: "Bank-4", recommendation: "Adjust refresh timing", priority: "Medium", confidence: 79, expectedYield: "+0.3%" },
];

export const lbistRecommendations: LbistRecRow[] = [
  { id: "LB-REC-001", logicBlock: "LB-GPU-118", recommendation: "Add transition margin pattern", priority: "Critical", confidence: 91, coverageGain: "+1.8%" },
  { id: "LB-REC-002", logicBlock: "LB-NOC-007", recommendation: "Extend LBIST coverage for NOC cluster", priority: "High", confidence: 88, coverageGain: "+1.2%" },
  { id: "LB-REC-003", logicBlock: "LB-CPU-042", recommendation: "Optimize MISR compression sequence", priority: "Medium", confidence: 82, coverageGain: "+0.6%" },
  { id: "LB-REC-004", logicBlock: "LB-DSP-089", recommendation: "Apply delay fault screening", priority: "Medium", confidence: 76, coverageGain: "+0.4%" },
];

export const waferRecommendations: WaferRecRow[] = [
  { id: "WF-REC-001", lotId: "LOT-2847", waferId: "W-12", recommendation: "Retest edge die cluster", priority: "Critical", confidence: 92, expectedYield: "+2.1%" },
  { id: "WF-REC-002", lotId: "LOT-2847", waferId: "W-08", recommendation: "Bin optimization for zone 3", priority: "High", confidence: 86, expectedYield: "+1.4%" },
  { id: "WF-REC-003", lotId: "LOT-2912", waferId: "W-04", recommendation: "Defect hotspot isolation", priority: "High", confidence: 84, expectedYield: "+0.9%" },
  { id: "WF-REC-004", lotId: "LOT-2912", waferId: "W-16", recommendation: "Spatial yield recovery pattern", priority: "Medium", confidence: 78, expectedYield: "+0.5%" },
];

export const bottomAISummary: BottomAISummary = {
  estimatedSavings: "$428K / month",
  yieldImprovement: "+5.8%",
  testTimeReduction: "-18.6s / lot",
  memoryRepairSuccess: "82.6%",
  logicCoverageIncrease: "+3.2%",
  patternReduction: "14 patterns",
  waferYieldIncrease: "+2.4%",
  totalRoi: "+24.8%",
};

export const scanFailureTrend: TrendPoint[] = [
  { label: "Mon", value: 48, value2: 12 }, { label: "Tue", value: 44, value2: 11 },
  { label: "Wed", value: 42, value2: 10 }, { label: "Thu", value: 38, value2: 9 },
  { label: "Fri", value: 36, value2: 8 }, { label: "Sat", value: 34, value2: 8 }, { label: "Sun", value: 32, value2: 7 },
];

export const chainHealthTrend: TrendPoint[] = [
  { label: "Healthy", value: 82 }, { label: "Warning", value: 12 }, { label: "Failing", value: 6 },
];

export const memoryFailureTrend: TrendPoint[] = [
  { label: "Mon", value: 28 }, { label: "Tue", value: 26 }, { label: "Wed", value: 24 },
  { label: "Thu", value: 22 }, { label: "Fri", value: 20 }, { label: "Sat", value: 19 }, { label: "Sun", value: 18 },
];

export const coverageTrendLbist: TrendPoint[] = [
  { label: "Mon", value: 93 }, { label: "Tue", value: 93.8 }, { label: "Wed", value: 94.2 },
  { label: "Thu", value: 94.8 }, { label: "Fri", value: 95.2 }, { label: "Sat", value: 95.6 }, { label: "Sun", value: 96.2 },
];

export const waferYieldTrend: TrendPoint[] = [
  { label: "Mon", value: 91.2 }, { label: "Tue", value: 91.8 }, { label: "Wed", value: 92.4 },
  { label: "Thu", value: 93 }, { label: "Fri", value: 93.6 }, { label: "Sat", value: 94 }, { label: "Sun", value: 94.2 },
];

export function generateWaferRecHeatmap(rows = 12, cols = 16): { value: number; row: number; col: number }[] {
  return generateGridHeatmap(rows, cols, 0.5, 0.5);
}

export const workflowSteps = [
  "Detected Issue",
  "AI Root Cause Analysis",
  "Recommendation Generated",
  "Engineer Review",
  "Approved",
  "Implemented",
  "Result Validation",
];

export const centerKPIs: CenterKPI[] = [
  { id: "redundant", title: "Redundant Patterns", value: "34 / 342", subtitle: "94% AI Confidence", description: "Duplicate or functionally redundant patterns detected.", change: -4.2, trend: "down", sparkline: [48, 44, 40, 38, 36, 35, 34], icon: "copy", positiveIsGood: false },
  { id: "removal", title: "Removal Recommended", value: "28", subtitle: "12.4% Test Time Reduction", description: "Patterns recommended for removal.", change: 6.8, trend: "up", sparkline: [18, 20, 22, 24, 25, 27, 28], icon: "trash-2", positiveIsGood: true },
  { id: "removal-conf", title: "Removal Confidence", value: "92%", status: "High Confidence", statusVariant: "success", description: "Average AI confidence.", change: 1.4, trend: "up", sparkline: [86, 87, 88, 89, 90, 91, 92], icon: "shield-check", positiveIsGood: true },
  { id: "reorder", title: "Reorder Recommendations", value: "42", subtitle: "5.8% Fault Escape Reduction", description: "Pattern execution sequence optimization.", change: 8.2, trend: "up", sparkline: [28, 32, 34, 36, 38, 40, 42], icon: "arrow-up-down", positiveIsGood: true },
  { id: "atpg", title: "ATPG Additions Suggested", value: "18", subtitle: "Coverage Improvement", description: "Additional ATPG patterns.", change: 12, trend: "up", sparkline: [10, 11, 12, 14, 15, 16, 18], icon: "plus-circle", positiveIsGood: true },
  { id: "fault-models", title: "Fault Models Targeted", value: "4", subtitle: "SA • TD • Bridging • Cell-Aware", status: "ACTIVE", statusVariant: "info", description: "Fault models addressed.", change: 0, trend: "up", sparkline: [4, 4, 4, 4, 4, 4, 4], icon: "target", positiveIsGood: true },
  { id: "low-power", title: "Low-Power Sets", value: "12", subtitle: "18% Switching Reduction", description: "Low-power scan pattern recommendations.", change: 9.6, trend: "up", sparkline: [6, 7, 8, 9, 10, 11, 12], icon: "zap-off", positiveIsGood: true },
  { id: "power-saving", title: "Estimated Power Saving", value: "21.6%", description: "Projected power reduction.", change: 3.2, trend: "up", sparkline: [14, 16, 17, 18, 19, 20, 21.6], icon: "battery-charging", positiveIsGood: true },
  { id: "coverage-delta", title: "Coverage Delta", value: "98.1% → 99.3%", status: "+1.2% Gain", statusVariant: "success", description: "Coverage after optimization.", change: 1.2, trend: "up", sparkline: [97.8, 98.0, 98.2, 98.4, 98.7, 99.0, 99.3], icon: "trending-up", positiveIsGood: true },
  { id: "total", title: "Total Recommendations", value: "104", subtitle: "Remove • Reorder • Add • Low Power", description: "Overall recommendation count.", change: 14.2, trend: "up", sparkline: [78, 84, 88, 92, 96, 100, 104], icon: "sparkles", positiveIsGood: true },
];

export const patternAgentMeta: AgentMeta = {
  title: "Pattern Recommendation Agent",
  responsibilities: [
    "Identify Redundant Patterns",
    "Recommend Pattern Removal",
    "Recommend Pattern Ordering",
    "Recommend Additional ATPG Patterns",
    "Recommend Low-Power Pattern Sets",
    "Coverage Improvement",
  ],
  inputs: ["Pattern Embeddings", "Coverage", "Similarity", "Fault Overlap"],
  outputs: ["Remove PAT_101", "Reorder Pattern Sequence", "Add Transition Patterns"],
};

export const scanDebugAgentMeta: AgentMeta = {
  title: "Scan Debug Recommendation Agent",
  responsibilities: [
    "Scan Chain Debug",
    "ATPG Constraint Review",
    "Timing Debug",
    "Power Debug",
    "Physical Defect Investigation",
  ],
  inputs: ["Failure Logs", "Diagnosis Results", "Fail Bitmaps", "Historical Cases"],
  outputs: ["Inspect Scan Chain 12", "Review Capture Clock", "Check IR Drop"],
};

export const testOptAgentMeta: AgentMeta = {
  title: "Test Optimization Recommendation Agent",
  responsibilities: [
    "Adaptive Testing",
    "Test Stop",
    "Risk-Based Testing",
    "Yield Optimization",
    "Cost Reduction",
    "Multi-Site Optimization",
  ],
  inputs: ["Yield", "ATE Logs", "Coverage", "Production History", "Pattern Recommendations"],
  outputs: ["Reduced Test Flow", "Stop at 98.8% Coverage", "Extended Testing"],
};

export const patternRecDistribution: HealthSegment[] = [
  { name: "Remove", value: 28, color: "#EF4444" },
  { name: "Reorder", value: 42, color: "#7C3AED" },
  { name: "ATPG", value: 18, color: "#06B6D4" },
  { name: "Low Power", value: 16, color: "#22C55E" },
];

export const patternCoverageTrend: TrendPoint[] = [
  { label: "W1", value: 98.1, value2: 98.4 },
  { label: "W2", value: 98.2, value2: 98.6 },
  { label: "W3", value: 98.3, value2: 98.8 },
  { label: "W4", value: 98.4, value2: 99.0 },
  { label: "W5", value: 98.5, value2: 99.1 },
  { label: "W6", value: 98.6, value2: 99.2 },
  { label: "W7", value: 98.1, value2: 99.3 },
];

export const patternRecRows: PatternRecRow[] = [
  { recommendationId: "PAT-REC-001", patternId: "PAT-9103", recommendation: "Remove legacy stuck-at pattern", priority: "High", confidence: 94, coverageGain: "N/A", powerSaving: "8%", status: "Pending" },
  { recommendationId: "PAT-REC-002", patternId: "PAT-4821", recommendation: "Reorder before transition block", priority: "Critical", confidence: 88, coverageGain: "+0.4%", powerSaving: "3%", status: "In Review" },
  { recommendationId: "PAT-REC-003", patternId: "PAT-NEW-018", recommendation: "Add bridge fault ATPG pattern", priority: "Critical", confidence: 92, coverageGain: "+2.6%", powerSaving: "5%", status: "Pending" },
  { recommendationId: "PAT-REC-004", patternId: "PAT-LP-012", recommendation: "Apply low-power scan set", priority: "Medium", confidence: 90, coverageGain: "+0.2%", powerSaving: "18%", status: "Approved" },
  { recommendationId: "PAT-REC-005", patternId: "PAT-8214", recommendation: "Merge with PAT-7892 cluster", priority: "Medium", confidence: 91, coverageGain: "+1.2%", powerSaving: "6%", status: "Pending" },
  { recommendationId: "PAT-REC-006", patternId: "PAT-3156", recommendation: "Reorder GPU cluster sequence", priority: "High", confidence: 87, coverageGain: "+0.8%", powerSaving: "4%", status: "Pending" },
];

export const rootCauseDistribution: HealthSegment[] = [
  { name: "Bridge Fault", value: 32, color: "#EF4444" },
  { name: "Clock Gating", value: 24, color: "#7C3AED" },
  { name: "Hold Violation", value: 18, color: "#06B6D4" },
  { name: "IR Drop", value: 14, color: "#F97316" },
  { name: "Unknown", value: 12, color: "#64748B" },
];

export const debugPriorityData: TrendPoint[] = [
  { label: "SC-004821", value: 94 },
  { label: "SC-007892", value: 88 },
  { label: "SC-003156", value: 82 },
  { label: "SC-002441", value: 76 },
  { label: "SC-009103", value: 68 },
];

export const failureCorrelationTrend: TrendPoint[] = [
  { label: "Mon", value: 72, value2: 84 },
  { label: "Tue", value: 74, value2: 86 },
  { label: "Wed", value: 76, value2: 88 },
  { label: "Thu", value: 78, value2: 90 },
  { label: "Fri", value: 80, value2: 91 },
  { label: "Sat", value: 81, value2: 92 },
  { label: "Sun", value: 82, value2: 94 },
];

export const scanDebugRecRows: ScanDebugRecRow[] = [
  { recommendationId: "DBG-REC-001", category: "Broken Chain", scanChain: "SC-004821", rootCause: "Bridge Fault", recommendation: "Inspect CDC boundary metal layer", priority: "Critical", confidence: 94, engineer: "Alex J.", status: "Pending", expectedImpact: "+1.2% yield" },
  { recommendationId: "DBG-REC-002", category: "Power", scanChain: "SC-007892", rootCause: "IR Drop", recommendation: "Check power grid near segment 4", priority: "High", confidence: 88, engineer: "Sarah M.", status: "In Review", expectedImpact: "Resolve 5 failing dies" },
  { recommendationId: "DBG-REC-003", category: "Timing", scanChain: "SC-003156", rootCause: "Hold Violation", recommendation: "Review capture clock timing", priority: "High", confidence: 86, engineer: "David K.", status: "Approved", expectedImpact: "-42 ps slack recovery" },
  { recommendationId: "DBG-REC-004", category: "ATPG Constraint", scanChain: "SC-002441", rootCause: "Constraint Conflict", recommendation: "Relax clock gating constraint", priority: "Medium", confidence: 82, engineer: "Priya R.", status: "Pending", expectedImpact: "+0.8% coverage" },
  { recommendationId: "DBG-REC-005", category: "Physical Defect", scanChain: "SC-009103", rootCause: "Metal Short", recommendation: "Run FIB isolation on suspect cell", priority: "Critical", confidence: 91, engineer: "Alex J.", status: "Pending", expectedImpact: "Confirm root cause" },
  { recommendationId: "DBG-REC-006", category: "Broken Chain", scanChain: "SC-001778", rootCause: "Chain Breakpoint", recommendation: "Re-stitch scan chain segment 7", priority: "Critical", confidence: 89, engineer: "Sarah M.", status: "In Review", expectedImpact: "Restore chain integrity" },
  { recommendationId: "DBG-REC-007", category: "Timing", scanChain: "SC-005632", rootCause: "Setup Violation", recommendation: "Add launch margin at flop 142", priority: "High", confidence: 84, engineer: "David K.", status: "Pending", expectedImpact: "Fix 8 transition fails" },
  { recommendationId: "DBG-REC-008", category: "Power", scanChain: "SC-008214", rootCause: "EM Violation", recommendation: "Reduce switching during scan shift", priority: "Medium", confidence: 80, engineer: "Priya R.", status: "Approved", expectedImpact: "18% power reduction" },
];

export const affectedScanChainsData: TrendPoint[] = [
  { label: "SC-004821", value: 42 },
  { label: "SC-007892", value: 38 },
  { label: "SC-003156", value: 32 },
  { label: "SC-002441", value: 28 },
  { label: "SC-009103", value: 24 },
];

export const yieldImprovementTrend: TrendPoint[] = [
  { label: "W1", value: 91.2, value2: 92.4 },
  { label: "W2", value: 91.8, value2: 93.0 },
  { label: "W3", value: 92.4, value2: 93.6 },
  { label: "W4", value: 93.0, value2: 94.2 },
  { label: "W5", value: 93.4, value2: 94.6 },
  { label: "W6", value: 93.8, value2: 95.0 },
  { label: "W7", value: 94.0, value2: 95.8 },
];

export const costReductionTrend: TrendPoint[] = [
  { label: "W1", value: 100, value2: 94 },
  { label: "W2", value: 100, value2: 91 },
  { label: "W3", value: 100, value2: 88 },
  { label: "W4", value: 100, value2: 85 },
  { label: "W5", value: 100, value2: 82 },
  { label: "W6", value: 100, value2: 79 },
  { label: "W7", value: 100, value2: 76 },
];

export const testTimeTrend: TrendPoint[] = [
  { label: "W1", value: 100, value2: 92 },
  { label: "W2", value: 100, value2: 89 },
  { label: "W3", value: 100, value2: 87 },
  { label: "W4", value: 100, value2: 85 },
  { label: "W5", value: 100, value2: 84 },
  { label: "W6", value: 100, value2: 82 },
  { label: "W7", value: 100, value2: 80 },
];

export const testOptRecRows: TestOptRecRow[] = [
  { recommendationId: "OPT-REC-001", optimizationType: "Adaptive Testing", currentValue: "Full flow", optimizedValue: "Risk-based flow", estimatedBenefit: "-18% test time", priority: "Critical", confidence: 92, status: "Pending", assignedEngineer: "Alex J." },
  { recommendationId: "OPT-REC-002", optimizationType: "Test Stop", currentValue: "100% patterns", optimizedValue: "Stop at 98.8%", estimatedBenefit: "$28K savings", priority: "High", confidence: 88, status: "In Review", assignedEngineer: "Sarah M." },
  { recommendationId: "OPT-REC-003", optimizationType: "Risk-Based", currentValue: "Uniform sampling", optimizedValue: "Prioritize high-risk", estimatedBenefit: "43 escapes prevented", priority: "High", confidence: 86, status: "Approved", assignedEngineer: "David K." },
  { recommendationId: "OPT-REC-004", optimizationType: "Yield Optimization", currentValue: "87.4% yield", optimizedValue: "90.5% yield", estimatedBenefit: "+3.1% yield", priority: "Critical", confidence: 91, status: "Pending", assignedEngineer: "Priya R." },
  { recommendationId: "OPT-REC-005", optimizationType: "Cost Reduction", currentValue: "$0.45/device", optimizedValue: "$0.38/device", estimatedBenefit: "$48K savings", priority: "High", confidence: 89, status: "Pending", assignedEngineer: "Alex J." },
  { recommendationId: "OPT-REC-006", optimizationType: "Multi-Site", currentValue: "Unbalanced load", optimizedValue: "Reassign Site 4-6", estimatedBenefit: "±2.3% correlation fix", priority: "Medium", confidence: 84, status: "In Review", assignedEngineer: "Sarah M." },
  { recommendationId: "OPT-REC-007", optimizationType: "Adaptive Testing", currentValue: "Static bin rules", optimizedValue: "Dynamic bin adjust", estimatedBenefit: "+1.2% yield", priority: "Medium", confidence: 82, status: "Pending", assignedEngineer: "David K." },
  { recommendationId: "OPT-REC-008", optimizationType: "Test Stop", currentValue: "No stop rules", optimizedValue: "6 hard stop rules", estimatedBenefit: "-12% runtime", priority: "High", confidence: 87, status: "Approved", assignedEngineer: "Priya R." },
];

export const roiAnalysisTrend: TrendPoint[] = [
  { label: "W1", value: 2.4, value2: 2.8 },
  { label: "W2", value: 2.6, value2: 3.0 },
  { label: "W3", value: 2.8, value2: 3.2 },
  { label: "W4", value: 3.0, value2: 3.4 },
  { label: "W5", value: 3.2, value2: 3.6 },
  { label: "W6", value: 3.4, value2: 3.7 },
  { label: "W7", value: 3.6, value2: 3.8 },
];

export const powerSavingTrend: TrendPoint[] = [
  { label: "W1", value: 100, value2: 92 },
  { label: "W2", value: 100, value2: 89 },
  { label: "W3", value: 100, value2: 86 },
  { label: "W4", value: 100, value2: 84 },
  { label: "W5", value: 100, value2: 81 },
  { label: "W6", value: 100, value2: 79 },
  { label: "W7", value: 100, value2: 78.4 },
];

export const patternClusterData: HealthSegment[] = [
  { name: "Cluster A", value: 34, color: "#7C3AED" },
  { name: "Cluster B", value: 28, color: "#06B6D4" },
  { name: "Cluster C", value: 22, color: "#F97316" },
  { name: "Cluster D", value: 16, color: "#EAB308" },
];

export const patternAgentKPIs: CenterKPI[] = centerKPIs;

export const scanDebugAgentKPIs: CenterKPI[] = [
  { id: "broken-chains", title: "Broken Chains Detected", value: "7", status: "3 Critical Priority", statusVariant: "danger", description: "Total scan chains identified with breakpoints requiring debug.", change: -2.1, trend: "down", sparkline: [12, 11, 10, 9, 8, 7, 7], icon: "unplug", positiveIsGood: false },
  { id: "debug-recs", title: "Debug Recommendations", value: "14", subtitle: "Isolation • Bypass • Re-Stitch", statusVariant: "info", description: "AI-generated scan chain debug recommendations.", change: 8.4, trend: "up", sparkline: [8, 9, 10, 11, 12, 13, 14], icon: "bug", positiveIsGood: true },
  { id: "avg-confidence", title: "Average Confidence", value: "88%", status: "Above 85% Threshold", statusVariant: "success", description: "Average AI confidence for generated recommendations.", change: 1.4, trend: "up", sparkline: [82, 83, 84, 85, 86, 87, 88], icon: "shield-check", positiveIsGood: true },
  { id: "constraint-violations", title: "Constraint Violations", value: "23", subtitle: "Across 6 Constraint Files", statusVariant: "warning", description: "Detected ATPG constraint violations.", change: -6.2, trend: "down", sparkline: [32, 30, 28, 26, 25, 24, 23], icon: "alert-triangle", positiveIsGood: false },
  { id: "review-recs", title: "Review Recommendations", value: "19", subtitle: "Relax • Tighten • Remove", statusVariant: "info", description: "Constraint optimization recommendations.", change: 4.8, trend: "up", sparkline: [12, 14, 15, 16, 17, 18, 19], icon: "clipboard-check", positiveIsGood: true },
  { id: "coverage-impact", title: "Coverage Impact", value: "+1.8%", status: "Projected After Applying Recommendations", statusVariant: "success", description: "Expected fault coverage improvement.", change: 1.8, trend: "up", sparkline: [0.4, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8], icon: "bar-chart-3", positiveIsGood: true },
  { id: "timing-violations", title: "Timing Violations", value: "11", status: "Setup 8 · Hold 3", statusVariant: "danger", description: "Detected setup and hold timing failures.", change: 1.2, trend: "up", sparkline: [8, 8, 9, 9, 10, 10, 11], icon: "clock-3", positiveIsGood: false },
  { id: "timing-debug-recs", title: "Timing Debug Recommendations", value: "16", subtitle: "At-Speed • Launch • Capture", statusVariant: "info", description: "Timing optimization recommendations.", change: 6.2, trend: "up", sparkline: [10, 11, 12, 13, 14, 15, 16], icon: "activity", positiveIsGood: true },
  { id: "worst-slack", title: "Worst Slack", value: "-42 ps", status: "Critical Path Flagged", statusVariant: "danger", description: "Worst timing slack detected.", change: -8.0, trend: "down", sparkline: [-28, -30, -32, -36, -38, -40, -42], icon: "trending-down", positiveIsGood: false },
  { id: "power-violations", title: "Power Violations", value: "9", status: "IR Drop 5 · EM 4", statusVariant: "warning", description: "Power integrity issues detected.", change: -2.0, trend: "down", sparkline: [14, 13, 12, 11, 10, 9, 9], icon: "zap-off", positiveIsGood: false },
  { id: "power-debug-recs", title: "Power Debug Recommendations", value: "12", subtitle: "Clock Gating • Domain Isolation", statusVariant: "info", description: "AI recommendations to reduce switching activity.", change: 5.4, trend: "up", sparkline: [6, 7, 8, 9, 10, 11, 12], icon: "battery-charging", positiveIsGood: true },
  { id: "peak-switching", title: "Peak Switching Activity", value: "74%", status: "Exceeds 65% Budget", statusVariant: "danger", description: "Maximum switching activity during scan testing.", change: 3.2, trend: "up", sparkline: [62, 64, 66, 68, 70, 72, 74], icon: "zap", positiveIsGood: false },
  { id: "defect-suspects", title: "Defect Suspects", value: "31", subtitle: "Across 4 Wafers", statusVariant: "warning", description: "Potential physical defect locations.", change: 4.1, trend: "up", sparkline: [22, 24, 26, 27, 28, 30, 31], icon: "search", positiveIsGood: false },
  { id: "investigation-recs", title: "Investigation Recommendations", value: "18", subtitle: "SEM • FIB • X-Ray • E-Beam", statusVariant: "info", description: "Recommended physical failure analysis.", change: 6.8, trend: "up", sparkline: [10, 12, 13, 14, 15, 16, 18], icon: "microscope", positiveIsGood: true },
  { id: "defect-localization", title: "Defect Localization Accuracy", value: "91%", status: "Average Across Suspects", statusVariant: "success", description: "AI accuracy for locating physical defects.", change: 1.6, trend: "up", sparkline: [86, 87, 88, 89, 89.5, 90, 91], icon: "locate-fixed", positiveIsGood: true },
];

export const scanDebugKPISections: KPISection[] = [
  {
    title: "Scan Chain Debug",
    kpis: scanDebugAgentKPIs.slice(0, 3),
  },
  {
    title: "ATPG Constraint Review",
    kpis: scanDebugAgentKPIs.slice(3, 6),
  },
  {
    title: "Timing Debug",
    kpis: scanDebugAgentKPIs.slice(6, 9),
  },
  {
    title: "Power Related Debug",
    kpis: scanDebugAgentKPIs.slice(9, 12),
  },
  {
    title: "Physical Defect Investigation",
    kpis: scanDebugAgentKPIs.slice(12, 15),
  },
];

export const failureRootCauseDistribution: HealthSegment[] = [
  { name: "Broken Chain", value: 28, color: "#EF4444" },
  { name: "Timing", value: 22, color: "#F97316" },
  { name: "Power", value: 18, color: "#EAB308" },
  { name: "ATPG Constraint", value: 16, color: "#7C3AED" },
  { name: "Physical Defect", value: 12, color: "#06B6D4" },
  { name: "Unknown", value: 4, color: "#64748B" },
];

export const debugRecommendationPriority: TrendPoint[] = [
  { label: "Critical", value: 8 },
  { label: "High", value: 14 },
  { label: "Medium", value: 18 },
  { label: "Low", value: 10 },
];

export const scanDebugRecommendationTrend: TrendPoint[] = [
  { label: "Day 1", value: 8 }, { label: "Day 5", value: 10 }, { label: "Day 10", value: 11 },
  { label: "Day 15", value: 12 }, { label: "Day 20", value: 13 }, { label: "Day 25", value: 14 }, { label: "Day 30", value: 14 },
];

export const scanDebugWorkflowSteps = [
  "Failure Logs",
  "Diagnosis Engine",
  "Root Cause Analysis",
  "Scan Debug Recommendation Agent",
  "Engineer Review",
  "Implementation",
  "Validation",
];

export const testOptAgentKPIs: CenterKPI[] = [
  { id: "adaptive-recs", title: "Adaptive Recommendations", value: "22", subtitle: "Flow • Sequence • Bin Adjustment", statusVariant: "neutral", description: "AI-generated adaptive testing recommendations.", change: 12.0, trend: "up", sparkline: [14, 16, 17, 18, 19, 21, 22], icon: "brain-circuit", positiveIsGood: true },
  { id: "test-time-red", title: "Test Time Reduction", value: "18%", status: "Projected if Fully Applied", statusVariant: "success", description: "Estimated reduction in total production test time.", change: 3.2, trend: "up", sparkline: [8, 10, 12, 13, 14, 16, 18], icon: "timer", positiveIsGood: true },
  { id: "flow-variants", title: "Flow Variants Evaluated", value: "8", subtitle: "Best Variant Selected", statusVariant: "info", description: "Number of optimized test flow variants evaluated.", change: 2.0, trend: "up", sparkline: [4, 5, 5, 6, 7, 7, 8], icon: "git-branch", positiveIsGood: true },
  { id: "stop-recs", title: "Stop Recommendations", value: "17", status: "Hard Stop 6 · Soft Stop 11", statusVariant: "warning", description: "AI recommendations for early test termination.", change: 5.4, trend: "up", sparkline: [10, 11, 12, 13, 14, 16, 17], icon: "square", positiveIsGood: true },
  { id: "escapes-prevented", title: "Escapes Prevented", value: "43", status: "Estimated with Stop Rules", statusVariant: "success", description: "Potential defective devices prevented from escaping.", change: 8.2, trend: "up", sparkline: [28, 32, 34, 36, 38, 40, 43], icon: "shield-check", positiveIsGood: true },
  { id: "active-stop-rules", title: "Active Stop Rules", value: "9", subtitle: "Lot • Wafer • Site • Bin", statusVariant: "info", description: "Configured adaptive stop rules.", change: 1.0, trend: "up", sparkline: [6, 6, 7, 7, 8, 8, 9], icon: "settings-2", positiveIsGood: true },
  { id: "high-risk-devices", title: "High-Risk Devices", value: "58", status: "Critical 12 · High 46", statusVariant: "danger", description: "Devices requiring additional testing.", change: 4.2, trend: "up", sparkline: [42, 44, 48, 50, 52, 55, 58], icon: "shield-alert", positiveIsGood: false },
  { id: "risk-recs", title: "Risk Recommendations", value: "24", subtitle: "Prioritize • Skip • Resample", statusVariant: "info", description: "AI-generated risk-based testing recommendations.", change: 6.8, trend: "up", sparkline: [14, 16, 18, 20, 21, 22, 24], icon: "clipboard-list", positiveIsGood: true },
  { id: "avg-risk-score", title: "Average Risk Score", value: "0.74", status: "Above 0.65 Threshold", statusVariant: "warning", description: "Average production risk score.", change: 0.06, trend: "up", sparkline: [0.62, 0.64, 0.66, 0.68, 0.70, 0.72, 0.74], icon: "activity", positiveIsGood: false },
  { id: "current-yield", title: "Current Yield", value: "87.4%", status: "+1.2% vs Last Lot", statusVariant: "success", description: "Current production yield.", change: 1.2, trend: "up", sparkline: [84, 85, 85.5, 86, 86.5, 87, 87.4], icon: "trending-up", positiveIsGood: true },
  { id: "yield-recs", title: "Yield Recommendations", value: "21", subtitle: "Bin • Limit • Retest Strategy", statusVariant: "info", description: "Yield improvement recommendations.", change: 7.2, trend: "up", sparkline: [12, 14, 16, 17, 18, 20, 21], icon: "target", positiveIsGood: true },
  { id: "projected-yield", title: "Projected Yield Gain", value: "+3.1%", status: "87.4% → 90.5%", statusVariant: "success", description: "Predicted yield improvement.", change: 3.1, trend: "up", sparkline: [0.4, 0.8, 1.2, 1.8, 2.2, 2.6, 3.1], icon: "arrow-up-circle", positiveIsGood: true },
  { id: "est-cost-saving", title: "Estimated Cost Saving", value: "$48K", status: "If Fully Applied", statusVariant: "success", description: "Estimated production cost reduction.", change: 8.6, trend: "up", sparkline: [24, 28, 32, 36, 40, 44, 48], icon: "dollar", positiveIsGood: true },
  { id: "cost-recs", title: "Cost Recommendations", value: "16", subtitle: "Handler • Probe • Retest", statusVariant: "info", description: "AI-generated cost optimization recommendations.", change: 5.2, trend: "up", sparkline: [8, 10, 11, 12, 13, 15, 16], icon: "wallet", positiveIsGood: true },
  { id: "cost-per-device", title: "Cost Per Device", value: "$0.38", status: "-$0.07 vs Last Lot", statusVariant: "success", description: "Average production test cost per device.", change: -7.0, trend: "down", sparkline: [0.48, 0.46, 0.44, 0.42, 0.40, 0.39, 0.38], icon: "coins", positiveIsGood: true },
  { id: "active-sites", title: "Active Test Sites", value: "16", status: "16 of 16 Configured", statusVariant: "info", description: "Configured multi-site test resources.", change: 0, trend: "up", sparkline: [16, 16, 16, 16, 16, 16, 16], icon: "network", positiveIsGood: true },
  { id: "site-recs", title: "Site Recommendations", value: "11", subtitle: "Load Balance • Disable • Reassign", statusVariant: "neutral", description: "AI recommendations for site optimization.", change: 4.8, trend: "up", sparkline: [6, 7, 8, 9, 9, 10, 11], icon: "git-merge", positiveIsGood: true },
  { id: "site-correlation", title: "Site Correlation Delta", value: "±2.3%", status: "3 Sites Outside ±1.5%", statusVariant: "warning", description: "Variation between test sites.", change: 0.4, trend: "up", sparkline: [1.2, 1.4, 1.6, 1.8, 2.0, 2.1, 2.3], icon: "bar-chart-4", positiveIsGood: false },
  { id: "total-opt-recs", title: "Total Recommendations", value: "111", subtitle: "Adaptive 22 · Stop 17 · Risk 24 · Yield 21 · Cost 16 · Site 11", description: "Total optimization recommendations generated.", change: 14.2, trend: "up", sparkline: [78, 84, 92, 96, 100, 106, 111], icon: "sparkles", positiveIsGood: true },
];

export const testOptKPISections: KPISection[] = [
  { title: "Adaptive Testing", kpis: testOptAgentKPIs.slice(0, 3) },
  { title: "Test Stop Optimization", kpis: testOptAgentKPIs.slice(3, 6) },
  { title: "Risk-Based Testing", kpis: testOptAgentKPIs.slice(6, 9) },
  { title: "Yield Optimization", kpis: testOptAgentKPIs.slice(9, 12) },
  { title: "Cost Reduction", kpis: testOptAgentKPIs.slice(12, 15) },
  { title: "Multi-Site Optimization", kpis: testOptAgentKPIs.slice(15, 18) },
  { title: "Summary", kpis: testOptAgentKPIs.slice(18, 19) },
];

export const adaptiveTestingDistribution: HealthSegment[] = [
  { name: "Adaptive", value: 22, color: "#7C3AED" },
  { name: "Stop Rules", value: 17, color: "#F97316" },
  { name: "Risk", value: 24, color: "#EF4444" },
  { name: "Yield", value: 21, color: "#22C55E" },
  { name: "Cost", value: 16, color: "#06B6D4" },
  { name: "Site", value: 11, color: "#EAB308" },
];

export const optimizationPriorityData: TrendPoint[] = [
  { label: "Critical", value: 18 },
  { label: "High", value: 32 },
  { label: "Medium", value: 38 },
  { label: "Low", value: 23 },
];

export const testOptRecommendationTrend: TrendPoint[] = [
  { label: "Day 1", value: 72 }, { label: "Day 5", value: 78 }, { label: "Day 10", value: 84 },
  { label: "Day 15", value: 90 }, { label: "Day 20", value: 98 }, { label: "Day 25", value: 105 }, { label: "Day 30", value: 111 },
];

export const testOptWorkflowSteps = [
  "Production History",
  "Yield Analytics",
  "ATE Logs",
  "AI Optimization Engine",
  "Test Optimization Recommendation Agent",
  "Engineer Approval",
  "Optimized Test Flow",
  "Production Validation",
];

export function generateSiteUtilizationHeatmap(rows = 4, cols = 4) {
  return generateGridHeatmap(rows, cols, 0.35, 0.65);
};

export const patternAgentSummary: AgentSummary = {
  title: "AI Summary",
  subtitle: "Pattern optimization impact from the recommendation agent",
  metrics: [
    { label: "Patterns to Remove", value: "28" },
    { label: "Patterns to Reorder", value: "42" },
    { label: "New ATPG Patterns", value: "18" },
    { label: "Coverage Gain", value: "+1.2%" },
    { label: "Power Saving", value: "21.6%" },
    { label: "Test Time Reduction", value: "12.4%" },
  ],
};

export const scanDebugAgentSummary: AgentSummary = {
  title: "AI Debug Executive Summary",
  subtitle: "Consolidated debug impact and projected improvements",
  metrics: [
    { label: "Broken Chains", value: "7" },
    { label: "Timing Issues", value: "11" },
    { label: "Power Issues", value: "9" },
    { label: "Constraint Violations", value: "23" },
    { label: "Physical Defects", value: "31" },
    { label: "Coverage Improvement", value: "+1.8%" },
    { label: "Estimated Yield Improvement", value: "+1.2%" },
    { label: "Expected Debug Time Reduction", value: "18.4 hrs" },
    { label: "AI Confidence", value: "88%" },
  ],
};

export const testOptAgentSummary: AgentSummary = {
  title: "Executive AI Summary",
  subtitle: "Projected optimization impact across all categories",
  metrics: [
    { label: "Adaptive Testing", value: "22 recs" },
    { label: "Yield Improvement", value: "+3.1%" },
    { label: "Test Time Reduction", value: "18%" },
    { label: "Cost Savings", value: "$48K" },
    { label: "Risk Reduction", value: "43 escapes" },
    { label: "Multi-Site Efficiency", value: "±2.3% delta" },
    { label: "Overall ROI", value: "3.8x" },
    { label: "AI Confidence", value: "92.4%" },
  ],
};

export const enterpriseExecutiveSummary: EnterpriseExecutiveSummary = {
  patternsRemoved: 28,
  coverageGain: "+1.2%",
  powerSaving: "21.6%",
  yieldImprovement: "+2.4%",
  testTimeReduction: "12.4%",
  costReduction: "$428K / quarter",
  roi: "3.8x",
  aiConfidence: "92.4%",
};

export const agentWorkflowSteps = [
  "Pattern Analysis",
  "Pattern Recommendation Agent",
  "Optimized Pattern Set",
  "Fault Analysis",
  "Scan Debug Recommendation Agent",
  "Debug Recommendation",
  "Production Data",
  "Test Optimization Recommendation Agent",
  "Adaptive Test Strategy",
];
