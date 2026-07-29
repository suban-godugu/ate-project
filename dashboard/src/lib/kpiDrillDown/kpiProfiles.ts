import type { KpiWidgetSpec, KpiWidgetType } from "@/types/kpiDrillDown";

export interface KpiProfile {
  id: string;
  widgetTypes: KpiWidgetType[];
  breakdownDimensions: string[];
}

export const KPI_PROFILES: Record<string, KpiProfile> = {
  "overall-health": {
    id: "health-analytics",
    widgetTypes: ["gauge", "heatmap", "radar", "pareto"],
    breakdownDimensions: ["fab", "tester", "product", "lot", "wafer", "module"],
  },
  "total-chains": {
    id: "chain-inventory",
    widgetTypes: ["treemap", "network", "histogram", "bar"],
    breakdownDimensions: ["module", "scanChain", "product", "tester"],
  },
  "healthy-chains": {
    id: "healthy-chain-analytics",
    widgetTypes: ["area", "wafer-map", "scatter", "line"],
    breakdownDimensions: ["lot", "wafer", "scanChain", "tester"],
  },
  "failing-chains": {
    id: "failure-analytics",
    widgetTypes: ["heatmap", "wafer-map", "correlation-matrix", "sankey"],
    breakdownDimensions: ["scanChain", "pattern", "lot", "wafer"],
  },
  "scan-coverage": {
    id: "coverage-analytics",
    widgetTypes: ["line", "gauge", "bubble", "similarity-matrix"],
    breakdownDimensions: ["pattern", "module", "vector", "product"],
  },
  "avg-diagnosis-confidence": {
    id: "diagnosis-confidence",
    widgetTypes: ["radar", "scatter", "network", "cluster"],
    breakdownDimensions: ["scanChain", "module", "tester", "pattern"],
  },
  "avg-test-time": {
    id: "runtime-analytics",
    widgetTypes: ["bar", "pareto", "timeline-mini", "distribution"],
    breakdownDimensions: ["tester", "pattern", "lot", "vector"],
  },
  "files-ingested": {
    id: "pattern-ingest-analytics",
    widgetTypes: ["treemap", "bar", "histogram", "timeline-mini"],
    breakdownDimensions: ["pattern", "vector", "product", "lot"],
  },
  "vectors-parsed": {
    id: "vector-parse-analytics",
    widgetTypes: ["gauge", "line", "area", "pareto"],
    breakdownDimensions: ["vector", "pattern", "tester", "module"],
  },
  "file-integrity": {
    id: "integrity-analytics",
    widgetTypes: ["gauge", "radar", "heatmap", "bar"],
    breakdownDimensions: ["pattern", "fab", "lot", "tester"],
  },
  "pattern-coverage-kpi": {
    id: "pattern-coverage-analytics",
    widgetTypes: ["line", "gauge", "similarity-matrix", "bubble"],
    breakdownDimensions: ["pattern", "module", "vector", "product"],
  },
  "metadata-extracted": {
    id: "metadata-analytics",
    widgetTypes: ["bar", "scatter", "network", "treemap"],
    breakdownDimensions: ["pattern", "vector", "product", "module"],
  },
  "embeddings-generated": {
    id: "embedding-analytics",
    widgetTypes: ["cluster", "scatter", "line", "histogram"],
    breakdownDimensions: ["pattern", "vector", "module", "product"],
  },
  "pattern-clusters": {
    id: "cluster-analytics",
    widgetTypes: ["cluster", "network", "similarity-matrix", "sankey"],
    breakdownDimensions: ["pattern", "vector", "module", "product"],
  },
  "redundant-patterns": {
    id: "redundancy-analytics",
    widgetTypes: ["pareto", "heatmap", "bar", "sankey"],
    breakdownDimensions: ["pattern", "vector", "module", "product"],
  },
  "similarity-analyses": {
    id: "similarity-analytics",
    widgetTypes: ["similarity-matrix", "scatter", "network", "bubble"],
    breakdownDimensions: ["pattern", "vector", "module", "tester"],
  },
  "pass-fail-linked": {
    id: "pass-fail-analytics",
    widgetTypes: ["heatmap", "wafer-map", "correlation-matrix", "stacked-bar"],
    breakdownDimensions: ["pattern", "lot", "wafer", "tester"],
  },
  "quality-reports": {
    id: "quality-report-analytics",
    widgetTypes: ["bar", "line", "distribution", "timeline-mini"],
    breakdownDimensions: ["pattern", "product", "lot", "tester"],
  },
  "imported-files": {
    id: "failure-import-analytics",
    widgetTypes: ["line", "bar", "gauge", "pareto", "timeline-mini"],
    breakdownDimensions: ["tester", "lot", "pattern", "product"],
  },
  "overall-failure-rate": {
    id: "failure-rate-analytics",
    widgetTypes: ["line", "wafer-map", "bar", "stacked-bar", "pareto"],
    breakdownDimensions: ["tester", "product", "lot", "wafer"],
  },
  "failing-patterns": {
    id: "failing-pattern-analytics",
    widgetTypes: ["bar", "histogram", "timeline-mini", "heatmap", "network"],
    breakdownDimensions: ["pattern", "module", "tester", "lot"],
  },
  "die-failure-rate": {
    id: "die-failure-analytics",
    widgetTypes: ["wafer-map", "heatmap", "scatter", "cluster", "histogram"],
    breakdownDimensions: ["die", "wafer", "lot", "module"],
  },
  "wafer-failure-rate": {
    id: "wafer-failure-analytics",
    widgetTypes: ["bar", "heatmap", "wafer-map", "line", "stacked-bar"],
    breakdownDimensions: ["wafer", "lot", "tester", "product"],
  },
  "lot-failure-rate": {
    id: "lot-failure-analytics",
    widgetTypes: ["bar", "line", "timeline-mini", "stacked-bar", "bar"],
    breakdownDimensions: ["lot", "tester", "product", "wafer"],
  },
  "fault-categories": {
    id: "fault-category-analytics",
    widgetTypes: ["bar", "pareto", "network", "line", "histogram"],
    breakdownDimensions: ["rootCause", "failureBin", "module", "pattern"],
  },
  "root-cause-confidence": {
    id: "rc-confidence-analytics",
    widgetTypes: ["gauge", "line", "bar", "scatter", "bar"],
    breakdownDimensions: ["rootCause", "pattern", "module", "tester"],
  },
  "recurring-failures": {
    id: "recurring-failure-analytics",
    widgetTypes: ["line", "bar", "timeline-mini", "wafer-map", "bubble"],
    breakdownDimensions: ["pattern", "lot", "wafer", "failureBin"],
  },
  "sd-failing-chains": {
    id: "sd-failing-chains-analytics",
    widgetTypes: ["network", "bar", "heatmap", "bar", "timeline-mini"],
    breakdownDimensions: ["scanChain", "pattern", "lot", "tester"],
  },
  "sd-failing-cells": {
    id: "sd-failing-cells-analytics",
    widgetTypes: ["heatmap", "histogram", "bar", "bar", "network"],
    breakdownDimensions: ["scanCell", "flop", "scanChain", "pattern"],
  },
  "sd-chain-breaks": {
    id: "sd-chain-breaks-analytics",
    widgetTypes: ["network", "bar", "histogram", "bar", "timeline-mini"],
    breakdownDimensions: ["scanChain", "scanCell", "pattern", "lot"],
  },
  "sd-shift-capture": {
    id: "sd-shift-capture-analytics",
    widgetTypes: ["stacked-bar", "histogram", "bar", "histogram", "heatmap"],
    breakdownDimensions: ["scanChain", "pattern", "tester", "lot"],
  },
  "sd-topology-chains": {
    id: "sd-topology-chains-analytics",
    widgetTypes: ["network", "cluster", "scatter", "radar", "bar"],
    breakdownDimensions: ["scanChain", "pattern", "module", "tester"],
  },
  "sd-chains-ranked": {
    id: "sd-chains-ranked-analytics",
    widgetTypes: ["bar", "bar", "histogram", "line", "bar"],
    breakdownDimensions: ["scanChain", "pattern", "lot", "tester"],
  },
  "sd-failure-correlations": {
    id: "sd-failure-correlations-analytics",
    widgetTypes: ["correlation-matrix", "similarity-matrix", "cluster", "heatmap", "bar"],
    breakdownDimensions: ["pattern", "scanChain", "lot", "wafer"],
  },
  "sd-top-failing-chain": {
    id: "sd-top-failing-chain-analytics",
    widgetTypes: ["network", "line", "timeline-mini", "bar", "bar"],
    breakdownDimensions: ["scanChain", "pattern", "lot", "wafer"],
  },
  "sd-diagnosis-reports": {
    id: "sd-diagnosis-reports-analytics",
    widgetTypes: ["bar", "line", "timeline-mini", "bar", "histogram"],
    breakdownDimensions: ["scanChain", "pattern", "lot", "tester"],
  },
  "sd-debug-locations": {
    id: "sd-debug-locations-analytics",
    widgetTypes: ["wafer-map", "scatter", "heatmap", "cluster", "bubble"],
    breakdownDimensions: ["die", "wafer", "scanCell", "scanChain"],
  },
  "sd-avg-confidence": {
    id: "sd-avg-confidence-analytics",
    widgetTypes: ["gauge", "line", "line", "bar", "scatter"],
    breakdownDimensions: ["scanChain", "pattern", "tester", "lot"],
  },
  "sd-pending-review": {
    id: "sd-pending-review-analytics",
    widgetTypes: ["bar", "bar", "histogram", "gauge", "timeline-mini"],
    breakdownDimensions: ["scanChain", "pattern", "lot", "tester"],
  },
  redundant: {
    id: "pa-redundant-analytics",
    widgetTypes: ["cluster", "similarity-matrix", "network", "bar", "heatmap"],
    breakdownDimensions: ["patternGroup", "pattern", "faultModel", "coverage"],
  },
  removal: {
    id: "pa-removal-analytics",
    widgetTypes: ["bar", "bar", "line", "histogram", "scatter"],
    breakdownDimensions: ["pattern", "coverage", "runtime", "tester"],
  },
  "removal-conf": {
    id: "pa-removal-conf-analytics",
    widgetTypes: ["gauge", "line", "bar", "bar", "scatter"],
    breakdownDimensions: ["pattern", "patternGroup", "tester", "lot"],
  },
  reorder: {
    id: "pa-reorder-analytics",
    widgetTypes: ["network", "bar", "bar", "sankey", "timeline-mini"],
    breakdownDimensions: ["pattern", "patternGroup", "runtime", "coverage"],
  },
  atpg: {
    id: "pa-atpg-analytics",
    widgetTypes: ["gauge", "bar", "heatmap", "bar", "scatter"],
    breakdownDimensions: ["faultModel", "coverage", "pattern", "compression"],
  },
  "fault-models": {
    id: "pa-fault-model-analytics",
    widgetTypes: ["bar", "bar", "radar", "line", "histogram"],
    breakdownDimensions: ["faultModel", "coverage", "pattern", "product"],
  },
  "low-power": {
    id: "pa-low-power-analytics",
    widgetTypes: ["stacked-bar", "bar", "bar", "line", "bubble"],
    breakdownDimensions: ["patternGroup", "pattern", "runtime", "tester"],
  },
  "power-saving": {
    id: "pa-power-saving-analytics",
    widgetTypes: ["stacked-bar", "bar", "bar", "line", "bubble"],
    breakdownDimensions: ["tester", "pattern", "runtime", "product"],
  },
  "coverage-delta": {
    id: "pa-coverage-delta-analytics",
    widgetTypes: ["line", "heatmap", "bar", "stacked-bar", "line"],
    breakdownDimensions: ["coverage", "pattern", "faultModel", "product"],
  },
  total: {
    id: "pa-total-rec-analytics",
    widgetTypes: ["bar", "line", "bar", "scatter", "timeline-mini"],
    breakdownDimensions: ["patternGroup", "pattern", "tester", "lot"],
  },
  "adaptive-recs": {
    id: "to-adaptive-recs-analytics",
    widgetTypes: ["bar", "gauge", "line", "line", "timeline-mini"],
    breakdownDimensions: ["testFlow", "testProgram", "product", "tester"],
  },
  "test-time-red": {
    id: "to-test-time-analytics",
    widgetTypes: ["bar", "stacked-bar", "bar", "histogram", "line"],
    breakdownDimensions: ["testFlow", "testProgram", "tester", "product"],
  },
  "flow-variants": {
    id: "to-flow-variants-analytics",
    widgetTypes: ["bar", "bar", "bar", "line", "radar"],
    breakdownDimensions: ["testFlow", "testProgram", "product", "tester"],
  },
  "stop-recs": {
    id: "to-stop-recs-analytics",
    widgetTypes: ["bar", "bar", "scatter", "bar", "histogram"],
    breakdownDimensions: ["lot", "wafer", "tester", "product"],
  },
  "escapes-prevented": {
    id: "to-escapes-analytics",
    widgetTypes: ["bar", "bar", "line", "timeline-mini", "stacked-bar"],
    breakdownDimensions: ["product", "lot", "wafer", "tester"],
  },
  "active-stop-rules": {
    id: "to-stop-rules-analytics",
    widgetTypes: ["bar", "bar", "histogram", "bar", "scatter"],
    breakdownDimensions: ["site", "tester", "lot", "product"],
  },
  "high-risk-devices": {
    id: "to-high-risk-analytics",
    widgetTypes: ["bar", "heatmap", "scatter", "bar", "line"],
    breakdownDimensions: ["product", "device", "lot", "wafer"],
  },
  "risk-recs": {
    id: "to-risk-recs-analytics",
    widgetTypes: ["bar", "bar", "scatter", "bar", "histogram"],
    breakdownDimensions: ["product", "device", "tester", "lot"],
  },
  "avg-risk-score": {
    id: "to-avg-risk-analytics",
    widgetTypes: ["gauge", "line", "histogram", "bar", "scatter"],
    breakdownDimensions: ["product", "lot", "tester", "device"],
  },
  "current-yield": {
    id: "to-current-yield-analytics",
    widgetTypes: ["line", "stacked-bar", "bar", "bar", "line"],
    breakdownDimensions: ["lot", "wafer", "product", "tester"],
  },
  "yield-recs": {
    id: "to-yield-recs-analytics",
    widgetTypes: ["bar", "bar", "line", "bar", "gauge"],
    breakdownDimensions: ["product", "lot", "tester", "testProgram"],
  },
  "projected-yield": {
    id: "to-projected-yield-analytics",
    widgetTypes: ["stacked-bar", "bar", "bar", "line", "bubble"],
    breakdownDimensions: ["product", "lot", "tester", "testProgram"],
  },
  "est-cost-saving": {
    id: "to-est-cost-analytics",
    widgetTypes: ["stacked-bar", "bar", "bar", "line", "bar"],
    breakdownDimensions: ["tester", "product", "site", "lot"],
  },
  "cost-recs": {
    id: "to-cost-recs-analytics",
    widgetTypes: ["bar", "line", "bar", "scatter", "gauge"],
    breakdownDimensions: ["tester", "product", "site", "testProgram"],
  },
  "cost-per-device": {
    id: "to-cost-per-device-analytics",
    widgetTypes: ["bar", "bar", "bar", "scatter", "stacked-bar"],
    breakdownDimensions: ["product", "lot", "tester", "device"],
  },
  "active-sites": {
    id: "to-active-sites-analytics",
    widgetTypes: ["bar", "bar", "bar", "heatmap", "line"],
    breakdownDimensions: ["site", "tester", "product", "testProgram"],
  },
  "site-recs": {
    id: "to-site-recs-analytics",
    widgetTypes: ["bar", "bar", "line", "bar", "scatter"],
    breakdownDimensions: ["site", "tester", "product", "testProgram"],
  },
  "site-correlation": {
    id: "to-site-correlation-analytics",
    widgetTypes: ["correlation-matrix", "similarity-matrix", "scatter", "bar", "line"],
    breakdownDimensions: ["site", "tester", "product", "lot"],
  },
  "total-opt-recs": {
    id: "to-total-recs-analytics",
    widgetTypes: ["bar", "line", "bar", "scatter", "timeline-mini"],
    breakdownDimensions: ["product", "tester", "testFlow", "site"],
  },
  "broken-chains": {
    id: "sd-broken-chains-analytics",
    widgetTypes: ["network", "network", "bar", "histogram", "scatter"],
    breakdownDimensions: ["scanChain", "pattern", "module", "tester"],
  },
  "debug-recs": {
    id: "sd-debug-recs-analytics",
    widgetTypes: ["bar", "bar", "bar", "scatter", "line"],
    breakdownDimensions: ["scanChain", "pattern", "tester", "lot"],
  },
  "avg-confidence": {
    id: "sd-avg-confidence-analytics",
    widgetTypes: ["gauge", "line", "bar", "bar", "scatter"],
    breakdownDimensions: ["scanChain", "pattern", "tester", "lot"],
  },
  "constraint-violations": {
    id: "sd-constraint-analytics",
    widgetTypes: ["treemap", "heatmap", "bar", "histogram", "scatter"],
    breakdownDimensions: ["pattern", "faultModel", "module", "tester"],
  },
  "review-recs": {
    id: "sd-review-recs-analytics",
    widgetTypes: ["bar", "bar", "timeline-mini", "bar", "histogram"],
    breakdownDimensions: ["pattern", "faultModel", "tester", "lot"],
  },
  "coverage-impact": {
    id: "sd-coverage-impact-analytics",
    widgetTypes: ["stacked-bar", "heatmap", "bar", "line", "stacked-bar"],
    breakdownDimensions: ["coverage", "pattern", "module", "faultModel"],
  },
  "timing-violations": {
    id: "sd-timing-viol-analytics",
    widgetTypes: ["histogram", "network", "scatter", "bar", "histogram"],
    breakdownDimensions: ["clockDomain", "pattern", "scanChain", "module"],
  },
  "timing-debug-recs": {
    id: "sd-timing-recs-analytics",
    widgetTypes: ["bar", "bar", "line", "network", "bar"],
    breakdownDimensions: ["clockDomain", "pattern", "scanChain", "tester"],
  },
  "worst-slack": {
    id: "sd-worst-slack-analytics",
    widgetTypes: ["line", "network", "bar", "scatter", "bar"],
    breakdownDimensions: ["clockDomain", "pattern", "scanChain", "module"],
  },
  "power-violations": {
    id: "sd-power-viol-analytics",
    widgetTypes: ["heatmap", "bar", "bar", "bar", "heatmap"],
    breakdownDimensions: ["powerDomain", "pattern", "module", "tester"],
  },
  "power-debug-recs": {
    id: "sd-power-recs-analytics",
    widgetTypes: ["stacked-bar", "bar", "bar", "line", "bar"],
    breakdownDimensions: ["powerDomain", "pattern", "module", "tester"],
  },
  "peak-switching": {
    id: "sd-peak-switch-analytics",
    widgetTypes: ["line", "heatmap", "bar", "bar", "line"],
    breakdownDimensions: ["clockDomain", "powerDomain", "pattern", "tester"],
  },
  "defect-suspects": {
    id: "sd-defect-suspects-analytics",
    widgetTypes: ["wafer-map", "scatter", "bar", "cluster", "line"],
    breakdownDimensions: ["wafer", "lot", "pattern", "scanChain"],
  },
  "investigation-recs": {
    id: "sd-investigation-analytics",
    widgetTypes: ["bar", "bar", "timeline-mini", "scatter", "bar"],
    breakdownDimensions: ["wafer", "lot", "pattern", "scanChain"],
  },
  "defect-localization": {
    id: "sd-defect-loc-analytics",
    widgetTypes: ["gauge", "scatter", "bar", "line", "bar"],
    breakdownDimensions: ["wafer", "lot", "pattern", "scanChain"],
  },
};

export const DEFAULT_KPI_PROFILE: KpiProfile = {
  id: "generic-analytics",
  widgetTypes: ["line", "bar", "heatmap", "gauge"],
  breakdownDimensions: ["product", "lot", "tester", "fab"],
};

export function getKpiProfile(kpiId: string): KpiProfile {
  return KPI_PROFILES[kpiId] ?? DEFAULT_KPI_PROFILE;
}

export function widgetSpan(type: KpiWidgetType): 1 | 2 {
  if (
    ["network", "correlation-matrix", "similarity-matrix", "sankey", "wafer-map", "heatmap", "cluster"].includes(type)
  ) {
    return 2;
  }
  return 1;
}

export function widgetHeight(type: KpiWidgetType): number {
  if (["network", "correlation-matrix", "similarity-matrix", "sankey", "cluster"].includes(type)) return 300;
  if (["wafer-map", "heatmap"].includes(type)) return 280;
  return 240;
}

const WIDGET_TITLES: Record<KpiWidgetType, string> = {
  line: "Metric Trajectory",
  area: "Trend Surface",
  bar: "Distribution Bars",
  scatter: "Confidence Scatter",
  heatmap: "Failure Density Heatmap",
  "wafer-map": "Wafer Spatial Map",
  gauge: "Target Attainment Gauge",
  histogram: "Value Histogram",
  pareto: "Failure Pareto",
  "stacked-bar": "Stacked Contribution",
  radar: "Multi-Axis Radar",
  "correlation-matrix": "Correlation Matrix",
  "similarity-matrix": "Pattern Similarity Matrix",
  network: "Dependency Network",
  "timeline-mini": "Micro Timeline",
  distribution: "Statistical Distribution",
  sankey: "Failure Flow Sankey",
  bubble: "Runtime Bubble Map",
  treemap: "Hierarchy Treemap",
  cluster: "Failure Cluster Map",
};

const DIAGNOSIS_WIDGET_TITLES: Record<string, string[]> = {
  "sd-failing-chains": ["Chain Topology Graph", "Top Failing Chains", "Failure Heatmap", "Chain Ranking", "Failure Timeline"],
  "sd-failing-cells": ["Cell Density Heatmap", "Scan Cell Histogram", "Clock Domain Analysis", "Cell Ranking", "Cell Dependency Graph"],
  "sd-chain-breaks": ["Chain Topology Graph", "Break Location Map", "Break Frequency", "Shift Direction", "Repair Suggestions"],
  "sd-shift-capture": ["Shift vs Capture Chart", "Timing Histogram", "Clock Analysis", "Cycle Distribution", "Failure Density"],
  "sd-topology-chains": ["Interactive Chain Topology", "Connected Graph", "Fan-in / Fan-out", "Clock Domains", "Path Explorer"],
  "sd-chains-ranked": ["Chain Ranking Table", "Failure Frequency", "Severity Distribution", "Failure Trend", "Historical Comparison"],
  "sd-failure-correlations": ["Correlation Matrix", "Pattern Similarity", "Failure Clusters", "Wafer Correlation", "Product Comparison"],
  "sd-top-failing-chain": ["Chain Topology Graph", "Chain History", "Pattern History", "Failure Timeline", "Affected Lots"],
  "sd-diagnosis-reports": ["Report History", "Report Versions", "Download Activity", "Review Status", "Report Timeline"],
  "sd-debug-locations": ["Die Map", "XY Coordinates", "Wafer Map", "Failure Hotspots", "Physical Layout"],
  "sd-avg-confidence": ["Confidence Gauge", "Confidence Trend", "AI Score History", "Manual Validation", "Historical Accuracy"],
  "sd-pending-review": ["Pending Diagnoses", "Engineer Assignment", "Priority Queue", "Confidence Score", "SLA Timer"],
  redundant: ["Duplicate Pattern Clusters", "Pattern Similarity Matrix", "Pattern Dependency Graph", "Runtime Savings", "Redundant Pattern Heatmap"],
  removal: ["Removal Priority Ranking", "Coverage Impact", "Runtime Reduction", "Risk Analysis", "AI Confidence"],
  "removal-conf": ["Confidence Gauge", "Historical Confidence Trend", "Engineer Approval Rate", "Success History", "AI Calibration"],
  reorder: ["Pattern Execution Flow", "Before vs After Ordering", "Runtime Comparison", "Dependency Graph", "AI Ranking"],
  atpg: ["Coverage Gap", "Suggested Patterns", "Fault Coverage", "ATPG Priority", "Historical Success"],
  "fault-models": ["Fault Model Distribution", "Coverage per Model", "Detection Rate", "Historical Comparison", "AI Recommendation"],
  "low-power": ["Power Before vs After", "Switching Activity", "Low Power Pattern List", "Energy Saving Trend", "Runtime Impact"],
  "power-saving": ["Power Waterfall", "Tester Power Usage", "Pattern Power Ranking", "Historical Savings", "AI Estimate"],
  "coverage-delta": ["Coverage Trend", "Coverage Heatmap", "Module Comparison", "Before vs After Coverage", "Historical Gain"],
  total: ["Recommendation Categories", "Monthly Trend", "Approval Rate", "Success History", "AI Effectiveness"],
  "adaptive-recs": ["Recommendation Ranking", "AI Confidence", "Historical Effectiveness", "Adaptive Learning Trend", "Improvement Timeline"],
  "test-time-red": ["Before vs After Runtime", "Runtime Waterfall", "Test Sequence Optimization", "Time Distribution", "Savings Projection"],
  "flow-variants": ["Flow Comparison", "Variant Ranking", "Success Rate", "Runtime Comparison", "Coverage Comparison"],
  "stop-recs": ["Hard Stop vs Soft Stop", "Yield Impact", "Escape Analysis", "Runtime Reduction", "Rule Effectiveness"],
  "escapes-prevented": ["Escape Categories", "Defect Distribution", "Historical Escapes", "Prevention Timeline", "Cost Avoidance"],
  "active-stop-rules": ["Rule Hierarchy", "Rule Utilization", "Trigger Frequency", "Rule Effectiveness", "Optimization Suggestions"],
  "high-risk-devices": ["Device Ranking", "Risk Heatmap", "Wafer Distribution", "Product Comparison", "Risk Timeline"],
  "risk-recs": ["Recommendation Priority", "Risk Reduction", "Business Impact", "Confidence", "Similar Cases"],
  "avg-risk-score": ["Risk Gauge", "Trend", "Distribution", "Product Comparison", "Threshold Analysis"],
  "current-yield": ["Yield Trend", "Yield Waterfall", "Wafer Comparison", "Lot Comparison", "AI Optimization Effect"],
  "yield-recs": ["Recommendation Ranking", "Yield Contribution", "Historical Improvements", "Success Rate", "AI Confidence"],
  "projected-yield": ["Before vs After Yield", "ROI Waterfall", "Production Gain", "Cost Impact", "Capacity Increase"],
  "est-cost-saving": ["Monthly Savings", "Annual Savings", "Cost Waterfall", "Cost by Tester", "Cost by Product"],
  "cost-recs": ["Recommendation Ranking", "Cost Reduction Trend", "ROI", "Historical Comparison", "AI Confidence"],
  "cost-per-device": ["Cost Breakdown", "Product Comparison", "Lot Comparison", "Tester Comparison", "Savings Simulation"],
  "active-sites": ["Site Comparison", "Utilization", "Throughput", "Site Ranking", "Capacity Planning"],
  "site-recs": ["Site Optimization", "Load Balancing", "Capacity Forecast", "AI Recommendation", "Historical Improvement"],
  "site-correlation": ["Correlation Matrix", "Site Similarity", "Cross-Site Comparison", "Yield Correlation", "Runtime Correlation"],
  "total-opt-recs": ["Recommendation Categories", "Approval Rate", "Success History", "Monthly Trend", "AI Performance"],
  "broken-chains": ["Chain Topology Graph", "Broken Chain Locations", "Chain Dependency Graph", "Failure Frequency", "Chain Health Score"],
  "debug-recs": ["Recommendation Priority", "AI Ranking", "Recommendation Categories", "Historical Success Rate", "Estimated Improvement"],
  "avg-confidence": ["Confidence Gauge", "AI Confidence Trend", "Manual Validation History", "Approval Percentage", "Calibration Analysis"],
  "constraint-violations": ["Constraint Hierarchy", "ATPG Constraint Tree", "Severity Distribution", "Violation Heatmap", "Suggested Fixes"],
  "review-recs": ["Pending Reviews", "Engineer Assignments", "Approval Workflow", "Status Timeline", "Comments"],
  "coverage-impact": ["Coverage Before vs After", "Coverage Heatmap", "Coverage by Module", "Coverage Trend", "Coverage Gain Waterfall"],
  "timing-violations": ["Setup/Hold Histogram", "Timing Path Graph", "Critical Path Visualization", "Clock Domain Analysis", "Slack Distribution"],
  "timing-debug-recs": ["Timing Optimization Ranking", "Recommended Fixes", "Timing Gain Estimate", "Clock Tree Comparison", "Validation History"],
  "worst-slack": ["Slack Trend", "Critical Timing Paths", "Timing Hierarchy", "Worst Path Explorer", "AI Optimization Suggestions"],
  "power-violations": ["IR Drop Heatmap", "Switching Activity", "Dynamic Power", "Leakage Power", "Power Hotspot Map"],
  "power-debug-recs": ["Before vs After Power", "Power Optimization Actions", "Estimated Savings", "Power Domain Analysis", "Historical Improvements"],
  "peak-switching": ["Activity Timeline", "Peak Windows", "Switching Heatmap", "Clock Domain Activity", "AI Recommendations"],
  "defect-suspects": ["Wafer Defect Map", "XY Coordinates", "Suspect Ranking", "Failure Clustering", "Historical Comparison"],
  "investigation-recs": ["Investigation Workflow", "Priority Ranking", "AI Confidence", "Similar Investigations", "Resolution History"],
  "defect-localization": ["Localization Accuracy Gauge", "Predicted vs Actual", "Wafer Comparison", "Confidence Trend", "Validation History"],
};

export function buildWidgetSpecs(kpiId: string, seed: number): KpiWidgetSpec[] {
  const profile = getKpiProfile(kpiId);
  let types = [...profile.widgetTypes];
  const customTitles = DIAGNOSIS_WIDGET_TITLES[kpiId];
  if (customTitles && types.includes("network")) {
    types = ["network", ...types.filter((t) => t !== "network")];
  }
  return types.map((type, i) => ({
    id: `${kpiId}-w-${i}`,
    type,
    title: customTitles?.[i] ?? WIDGET_TITLES[type],
    span: widgetSpan(type),
    height: type === "network" && customTitles ? 320 : widgetHeight(type),
    data: { seed: seed + i * 17, kpiId, type },
  }));
}
