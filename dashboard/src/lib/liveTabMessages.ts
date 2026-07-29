/** Per-module empty-state copy for live mode (P1-8). */
export const LIVE_EMPTY_MESSAGES: Record<string, Record<string, { title: string; description: string }>> = {
  executive: {
    overview: {
      title: "No executive dashboard data",
      description: "Upload test data or adjust filters to populate KPIs and patterns.",
    },
  },
  "scan-chain": {
    overview: { title: "No Scan Chain data", description: "Upload STDF or ATE log files, or adjust filters." },
    "pattern-analysis": {
      title: "Pattern Analysis Agent unavailable",
      description: "Start the Pattern Analysis Agent service to embed its dashboard here.",
    },
    "failure-analysis": {
      title: "Failure Analysis Agent unavailable",
      description: "Start the Failure Analysis Agent service to embed its dashboard here.",
    },
    "scan-diagnosis": {
      title: "Scan Diagnosis Agent unavailable",
      description: "Start the Scan Diagnosis Agent service to embed its dashboard here.",
    },
  },
  mbist: {
    overview: { title: "No MBIST data", description: "No memory BIST results for the selected filters." },
    "memory-health": { title: "No memory health data", description: "No MBIST health metrics available." },
    "failure-analysis": { title: "No MBIST failures", description: "No memory failures recorded." },
    diagnosis: { title: "No MBIST diagnosis data", description: "No diagnosis reports found." },
    "ai-recommendation": { title: "No MBIST recommendations", description: "No AI recommendations generated yet." },
  },
  lbist: {
    overview: { title: "No LBIST data", description: "No logic BIST results for the selected filters." },
    "coverage-analysis": { title: "No coverage data", description: "No LBIST coverage metrics available." },
    "failure-analysis": { title: "No LBIST failures", description: "No logic failures recorded." },
    diagnosis: { title: "No LBIST diagnosis data", description: "No diagnosis reports found." },
    "ai-recommendation": { title: "No LBIST recommendations", description: "No AI recommendations generated yet." },
  },
  "wafer-analysis": {
    overview: { title: "No wafer analysis data", description: "Upload wafer defect data or adjust filters." },
    centre: { title: "No centre defect data", description: "No wafer uploads classified as centre defects." },
    donut: { title: "No donut defect data", description: "No wafer uploads in this defect class." },
    "edge-ring": { title: "No edge-ring defect data", description: "No wafer uploads in this defect class." },
    scratch: { title: "No scratch defect data", description: "No wafer uploads in this defect class." },
    "near-full": { title: "No near-full defect data", description: "No wafer uploads in this defect class." },
    normal: { title: "No normal wafer data", description: "No normal-class wafer uploads found." },
    "edge-loc": { title: "No edge-loc defect data", description: "No wafer uploads in this defect class." },
    local: { title: "No local defect data", description: "No wafer uploads in this defect class." },
    random: { title: "No random defect data", description: "No wafer uploads in this defect class." },
  },
  "cost-intelligence": {
    overview: { title: "No cost data", description: "No cost intelligence records for the selected filters." },
    "scan-chain": { title: "No scan chain cost data", description: "No scan chain cost breakdown available." },
    mbist: { title: "No MBIST cost data", description: "No MBIST cost records found." },
    lbist: { title: "No LBIST cost data", description: "No LBIST cost records found." },
    wafer: { title: "No wafer cost data", description: "No wafer cost records found." },
    "ai-optimization": { title: "No cost optimization data", description: "No AI cost recommendations available." },
  },
  alerts: {
    overview: { title: "No alerts", description: "No alerts match the current filters." },
    "scan-chain": { title: "No scan chain alerts", description: "No alerts from Scan Chain module." },
    mbist: { title: "No MBIST alerts", description: "No alerts from MBIST module." },
    lbist: { title: "No LBIST alerts", description: "No alerts from LBIST module." },
    wafer: { title: "No wafer alerts", description: "No alerts from Wafer Analysis module." },
    cost: { title: "No cost alerts", description: "No alerts from Cost Intelligence module." },
    "ai-recommendation": { title: "No recommendation alerts", description: "No alerts from Recommendation Analysis." },
  },
  "recommendation-analysis": {
    overview: { title: "No recommendations", description: "No unified recommendations for the selected filters." },
    "pattern-agent": { title: "No pattern recommendations", description: "No Pattern Agent recommendations in the database." },
    "scan-debug-agent": { title: "No scan debug recommendations", description: "No Scan Debug recommendations in the database." },
    "test-optimization-agent": { title: "No test optimization recommendations", description: "No Test Optimization recommendations in the database." },
    "scan-chain": { title: "No scan chain recommendations", description: "No recommendations for Scan Chain." },
    mbist: { title: "No MBIST recommendations", description: "No recommendations for MBIST." },
    lbist: { title: "No LBIST recommendations", description: "No recommendations for LBIST." },
    wafer: { title: "No wafer recommendations", description: "No recommendations for Wafer Analysis." },
  },
};

export function getLiveEmptyMessage(module: string, tab: string) {
  return (
    LIVE_EMPTY_MESSAGES[module]?.[tab] ?? {
      title: "No data available",
      description: "Try adjusting filters or upload new test data.",
    }
  );
}
