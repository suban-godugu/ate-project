import { chainHealthData, executiveOverviewKPIs } from "@/lib/scanChainData";
import type {
  TotalScanChainsProps,
  DistributionTabId,
  BreakdownTabId,
} from "@/components/scan-chain/kpi-drilldowns/TotalScanChainsDrillCard";

const MODULE_DISTRIBUTION = [
  { module: "M1-Core", count: 1293 },
  { module: "M3-IO", count: 1140 },
  { module: "M5-Cache", count: 715 },
];

const PRODUCT_DISTRIBUTION = [
  { module: "Orion-X", count: 1180 },
  { module: "Nova-SoC", count: 982 },
  { module: "Atlas-IO", count: 771 },
];

const FAB_DISTRIBUTION = [
  { module: "Fab-12", count: 1540 },
  { module: "Fab-18", count: 892 },
  { module: "Fab-22", count: 501 },
];

const TESTER_DISTRIBUTION = [
  { module: "V93000-S1", count: 1320 },
  { module: "UltraFlex-H2", count: 1014 },
  { module: "J750-EX", count: 599 },
];

const LOT_DISTRIBUTION = [
  { module: "LOT-A24-118", count: 860 },
  { module: "LOT-B24-204", count: 1120 },
  { module: "LOT-C24-077", count: 953 },
];

const MODULE_BREAKDOWN = [
  { name: "M1-Core", value: 1293, delta: 4.6 },
  { name: "M3-IO", value: 1140, delta: 0.9 },
  { name: "M5-Cache", value: 715, delta: 3.4 },
];

const SCAN_CHAIN_BREAKDOWN = [
  { name: "SC-CPU-0", value: 412, delta: 2.1 },
  { name: "SC-IO-N", value: 368, delta: -1.2 },
  { name: "SC-MEM-S", value: 295, delta: 5.3 },
];

const PRODUCT_BREAKDOWN = [
  { name: "Orion-X", value: 1180, delta: 3.8 },
  { name: "Nova-SoC", value: 982, delta: 1.4 },
  { name: "Atlas-IO", value: 771, delta: -0.6 },
];

const TESTER_BREAKDOWN = [
  { name: "V93000-S1", value: 1320, delta: 2.7 },
  { name: "UltraFlex-H2", value: 1014, delta: 0.5 },
  { name: "J750-EX", value: 599, delta: -2.1 },
];

const FAB_BREAKDOWN = [
  { name: "Fab-12", value: 1540, delta: 4.1 },
  { name: "Fab-18", value: 892, delta: 1.8 },
  { name: "Fab-22", value: 501, delta: -0.9 },
];

const LOT_BREAKDOWN = [
  { name: "LOT-A24-118", value: 860, delta: 3.2 },
  { name: "LOT-B24-204", value: 1120, delta: 2.0 },
  { name: "LOT-C24-077", value: 953, delta: -1.4 },
];

/** Build drill-down props from scan-chain mock data (replace with API mapper later). */
export function buildTotalScanChainsDrillProps(): TotalScanChainsProps {
  const kpi = executiveOverviewKPIs.find((item) => item.id === "total-chains");
  const totalChains = chainHealthData.reduce((sum, seg) => sum + seg.value, 0);
  const disabledChains = 42;
  const activeChains = totalChains - disabledChains;
  const growth = kpi?.change ?? 0;

  const distributionByTab: Record<DistributionTabId, typeof MODULE_DISTRIBUTION> = {
    Module: MODULE_DISTRIBUTION,
    Product: PRODUCT_DISTRIBUTION,
    Fab: FAB_DISTRIBUTION,
    Tester: TESTER_DISTRIBUTION,
    Lot: LOT_DISTRIBUTION,
  };

  const breakdownByTab: Record<BreakdownTabId, typeof MODULE_BREAKDOWN> = {
    Module: MODULE_BREAKDOWN,
    "Scan Chain": SCAN_CHAIN_BREAKDOWN,
    Product: PRODUCT_BREAKDOWN,
    Tester: TESTER_BREAKDOWN,
    Fab: FAB_BREAKDOWN,
    Lot: LOT_BREAKDOWN,
  };

  return {
    totalChains,
    activeChains,
    disabledChains,
    growth,
    businessImpact: growth >= 3 ? "High" : growth >= 1 ? "Moderate" : "Low",
    operationalStatus: disabledChains / totalChains > 0.08 ? "Warning" : "Healthy",
    distribution: distributionByTab.Module,
    distributionByTab,
    compressionRatio: 42.8,
    chainLengthDistribution: [
      { range: "50–100", value: 420 },
      { range: "100–150", value: 980 },
      { range: "150–200", value: 1120 },
      { range: "200+", value: 413 },
    ],
    breakdown: breakdownByTab.Module,
    breakdownByTab,
  };
}
