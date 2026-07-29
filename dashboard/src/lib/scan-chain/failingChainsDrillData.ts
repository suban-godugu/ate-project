import { chainHealthData, executiveOverviewKPIs } from "@/lib/scanChainData";
import type {
  BreakdownTabId,
  FailingChainsProps,
} from "@/components/scan-chain/kpi-drilldowns/FailingChainsDrillCard";

const SCAN_CHAIN_BREAKDOWN = [
  { category: "Scan Chain", name: "SC-004821", failingChains: 63, delta: 4.9, share: 40.0 },
  { category: "Scan Chain", name: "SC-009144", failingChains: 38, delta: 2.1, share: 24.1 },
  { category: "Scan Chain", name: "SC-002317", failingChains: 24, delta: -1.8, share: 15.2 },
];

const PATTERN_BREAKDOWN = [
  { category: "Pattern", name: "PAT-ATPG-12", failingChains: 41, delta: 3.6, share: 28.9 },
  { category: "Pattern", name: "PAT-SCAN-08", failingChains: 34, delta: 1.2, share: 23.9 },
  { category: "Pattern", name: "PAT-MBIST-03", failingChains: 22, delta: -2.4, share: 15.5 },
];

const LOT_BREAKDOWN = [
  { category: "Lot", name: "LOT-A2847", failingChains: 52, delta: 5.2, share: 36.6 },
  { category: "Lot", name: "LOT-B2848", failingChains: 44, delta: 0.8, share: 31.0 },
  { category: "Lot", name: "LOT-C2849", failingChains: 28, delta: -3.1, share: 19.7 },
];

const WAFER_BREAKDOWN = [
  { category: "Wafer", name: "W-12-044", failingChains: 36, delta: 2.7, share: 25.4 },
  { category: "Wafer", name: "W-12-045", failingChains: 31, delta: -0.9, share: 21.8 },
  { category: "Wafer", name: "W-18-019", failingChains: 48, delta: 4.4, share: 33.8 },
];

const TESTER_BREAKDOWN = [
  { category: "Tester", name: "V93000-S1", failingChains: 58, delta: 3.1, share: 40.8 },
  { category: "Tester", name: "UltraFlex-H2", failingChains: 46, delta: 1.5, share: 32.4 },
  { category: "Tester", name: "J750-EX", failingChains: 21, delta: -2.2, share: 14.8 },
];

const MODULE_BREAKDOWN = [
  { category: "Module", name: "M1-Core", failingChains: 64, delta: 4.2, share: 45.1 },
  { category: "Module", name: "M3-IO", failingChains: 48, delta: 0.6, share: 33.8 },
  { category: "Module", name: "M5-Cache", failingChains: 30, delta: -1.4, share: 21.1 },
];

/** Build drill-down props from scan-chain mock data (replace with API mapper later). */
export function buildFailingChainsDrillProps(): FailingChainsProps {
  const kpi = executiveOverviewKPIs.find((item) => item.id === "failing-chains");
  const failingChains = chainHealthData.find((s) => s.name === "Failing")?.value ?? 0;
  const totalChains = chainHealthData.reduce((sum, seg) => sum + seg.value, 0);
  const failureRatio = totalChains > 0 ? (failingChains / totalChains) * 100 : 0;
  const changeVsPreviousLot = kpi?.change ?? 0;

  const breakdownByTab: Record<BreakdownTabId, typeof SCAN_CHAIN_BREAKDOWN> = {
    "Scan Chain": SCAN_CHAIN_BREAKDOWN,
    Pattern: PATTERN_BREAKDOWN,
    Lot: LOT_BREAKDOWN,
    Wafer: WAFER_BREAKDOWN,
    Tester: TESTER_BREAKDOWN,
    Module: MODULE_BREAKDOWN,
  };

  return {
    failingChains,
    failureRatio,
    newlyDetectedFailures: 16,
    changeVsPreviousLot,
    businessImpact: failureRatio >= 6 ? "Critical" : failureRatio >= 4 ? "High" : "Moderate",
    operationalStatus: failureRatio >= 5 ? "Fab Hold" : failureRatio >= 4 ? "Warning" : "Monitor",
    failureStatus: {
      critical: 28,
      active: 114,
      underInvestigation: 22,
    },
    breakdown: breakdownByTab["Scan Chain"],
    breakdownByTab,
  };
}
