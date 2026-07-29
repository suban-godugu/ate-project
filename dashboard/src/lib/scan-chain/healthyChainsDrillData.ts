import { chainHealthData, executiveOverviewKPIs } from "@/lib/scanChainData";
import type {
  BreakdownTabId,
  DistributionTabId,
  HealthyChainsProps,
} from "@/components/scan-chain/kpi-drilldowns/HealthyChainsDrillCard";

const MODULE_DISTRIBUTION = [
  { category: "Module", name: "M1-Core", value: 1032, percentage: 45.2 },
  { category: "Module", name: "M3-IO", value: 784, percentage: 34.3 },
  { category: "Module", name: "M5-Cache", value: 468, percentage: 20.5 },
];

const PRODUCT_DISTRIBUTION = [
  { category: "Product", name: "Orion-X", value: 940, percentage: 41.2 },
  { category: "Product", name: "Nova-SoC", value: 812, percentage: 35.5 },
  { category: "Product", name: "Atlas-IO", value: 532, percentage: 23.3 },
];

const FAB_DISTRIBUTION = [
  { category: "Fab", name: "Fab-12", value: 1210, percentage: 53.0 },
  { category: "Fab", name: "Fab-18", value: 684, percentage: 29.9 },
  { category: "Fab", name: "Fab-22", value: 390, percentage: 17.1 },
];

const TESTER_DISTRIBUTION = [
  { category: "Tester", name: "V93000-S1", value: 1024, percentage: 44.8 },
  { category: "Tester", name: "UltraFlex-H2", value: 798, percentage: 34.9 },
  { category: "Tester", name: "J750-EX", value: 462, percentage: 20.2 },
];

const LOT_DISTRIBUTION = [
  { category: "Lot", name: "LOT-A2847", value: 924, percentage: 40.5 },
  { category: "Lot", name: "LOT-B2848", value: 760, percentage: 33.3 },
  { category: "Lot", name: "LOT-C2849", value: 600, percentage: 26.3 },
];

const WAFER_DISTRIBUTION = [
  { category: "Wafer", name: "W-12-044", value: 612, percentage: 26.8 },
  { category: "Wafer", name: "W-12-045", value: 588, percentage: 25.7 },
  { category: "Wafer", name: "W-18-019", value: 1084, percentage: 47.5 },
];

const MODULE_BREAKDOWN = [
  { category: "Module", name: "M1-Core", healthyChains: 1032, delta: 4.1, share: 45.2 },
  { category: "Module", name: "M3-IO", healthyChains: 784, delta: 1.8, share: 34.3 },
  { category: "Module", name: "M5-Cache", healthyChains: 468, delta: 2.6, share: 20.5 },
];

const PRODUCT_BREAKDOWN = [
  { category: "Product", name: "Orion-X", healthyChains: 940, delta: 3.4, share: 41.2 },
  { category: "Product", name: "Nova-SoC", healthyChains: 812, delta: 2.2, share: 35.5 },
  { category: "Product", name: "Atlas-IO", healthyChains: 532, delta: -0.8, share: 23.3 },
];

const FAB_BREAKDOWN = [
  { category: "Fab", name: "Fab-12", healthyChains: 1210, delta: 3.8, share: 53.0 },
  { category: "Fab", name: "Fab-18", healthyChains: 684, delta: 1.5, share: 29.9 },
  { category: "Fab", name: "Fab-22", healthyChains: 390, delta: -1.1, share: 17.1 },
];

const TESTER_BREAKDOWN = [
  { category: "Tester", name: "V93000-S1", healthyChains: 1024, delta: 2.9, share: 44.8 },
  { category: "Tester", name: "UltraFlex-H2", healthyChains: 798, delta: 0.7, share: 34.9 },
  { category: "Tester", name: "J750-EX", healthyChains: 462, delta: -1.6, share: 20.2 },
];

const LOT_BREAKDOWN = [
  { category: "Lot", name: "LOT-A2847", healthyChains: 924, delta: 3.2, share: 40.5 },
  { category: "Lot", name: "LOT-B2848", healthyChains: 760, delta: 1.9, share: 33.3 },
  { category: "Lot", name: "LOT-C2849", healthyChains: 600, delta: -0.5, share: 26.3 },
];

const WAFER_BREAKDOWN = [
  { category: "Wafer", name: "W-12-044", healthyChains: 612, delta: 2.4, share: 26.8 },
  { category: "Wafer", name: "W-12-045", healthyChains: 588, delta: 1.1, share: 25.7 },
  { category: "Wafer", name: "W-18-019", healthyChains: 1084, delta: 4.0, share: 47.5 },
];

/** Build drill-down props from scan-chain mock data (replace with API mapper later). */
export function buildHealthyChainsDrillProps(): HealthyChainsProps {
  const kpi = executiveOverviewKPIs.find((item) => item.id === "healthy-chains");
  const healthyChains = chainHealthData.find((s) => s.name === "Healthy")?.value ?? 0;
  const totalChains = chainHealthData.reduce((sum, seg) => sum + seg.value, 0);
  const healthyRatio = totalChains > 0 ? (healthyChains / totalChains) * 100 : 0;
  const growth = kpi?.change ?? 0;
  const recoveredChains = 38;
  const monitoringChains = 126;

  const distributionByTab: Record<DistributionTabId, typeof MODULE_DISTRIBUTION> = {
    Module: MODULE_DISTRIBUTION,
    Product: PRODUCT_DISTRIBUTION,
    Fab: FAB_DISTRIBUTION,
    Tester: TESTER_DISTRIBUTION,
    Lot: LOT_DISTRIBUTION,
    Wafer: WAFER_DISTRIBUTION,
  };

  const breakdownByTab: Record<BreakdownTabId, typeof MODULE_BREAKDOWN> = {
    Module: MODULE_BREAKDOWN,
    Product: PRODUCT_BREAKDOWN,
    Fab: FAB_BREAKDOWN,
    Tester: TESTER_BREAKDOWN,
    Lot: LOT_BREAKDOWN,
    Wafer: WAFER_BREAKDOWN,
  };

  return {
    healthyChains,
    healthyRatio,
    recoveredChains,
    growth,
    businessImpact: healthyRatio >= 80 ? "Low" : healthyRatio >= 75 ? "Moderate" : "High",
    operationalStatus: healthyRatio >= 78 ? "Healthy" : healthyRatio >= 70 ? "Monitor" : "Warning",
    distribution: distributionByTab.Module,
    distributionByTab,
    status: {
      healthy: healthyChains,
      recovered: recoveredChains,
      monitoring: monitoringChains,
    },
    breakdown: breakdownByTab.Lot,
    breakdownByTab,
    diagnosis: {
      confidence: 87,
      summary:
        "Healthy scan chains maintain stable signal integrity, balanced scan lengths, high scan coverage, and no recurring bridge/open defects. Recent repair actions and ATPG optimization have successfully restored chain integrity and improved overall stability.",
      healthFactors: [
        "Stable Scan Coverage",
        "Balanced Chain Length",
        "No Critical Faults Detected",
        "ATPG Patterns Passed",
        "Consistent Tester Performance",
        "Successful Repair Validation",
        "Compression Within Target Range",
        "Low Re-test Rate",
      ],
      healthyComponents: ["Modules", "Products", "Lots", "Wafers", "Testers", "Scan Chains"],
    },
  };
}
