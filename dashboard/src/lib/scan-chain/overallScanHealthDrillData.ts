import {
  chainHealthData,
  executiveOverviewKPIs,
} from "@/lib/scanChainData";
import type { OverallScanHealthProps } from "@/components/scan-chain/kpi-drilldowns/OverallScanHealthDrillCard";

/** Build drill-down props from scan-chain mock data (replace with API mapper later). */
export function buildOverallScanHealthDrillProps(): OverallScanHealthProps {
  const kpi = executiveOverviewKPIs.find((item) => item.id === "overall-health");
  const healthyChains = chainHealthData.find((s) => s.name === "Healthy")?.value ?? 0;
  const failingChains = chainHealthData.find((s) => s.name === "Failing")?.value ?? 0;
  const unknownChains = chainHealthData.find((s) => s.name === "Unknown")?.value ?? 0;
  const totalChains = chainHealthData.reduce((sum, seg) => sum + seg.value, 0);
  const currentHealth = totalChains > 0 ? (healthyChains / totalChains) * 100 : 0;
  const targetHealth = 80;
  const trend = kpi?.change ?? 0;
  const gap = currentHealth - targetHealth;

  return {
    currentHealth,
    targetHealth,
    trend,
    gap,
    status: gap >= 0 ? "On Target" : "Below Target",
    risk: gap <= -5 ? "High" : gap <= -2 ? "Moderate" : "Low",
    businessImpact: gap <= -5 ? "Critical" : gap <= -2 ? "Moderate" : "Low",
    operationalPriority: gap <= -5 ? "Immediate" : gap <= -2 ? "Monitor" : "Stable",
    healthyChains,
    failingChains,
    unknownChains,
    breakdown: [
      { metric: "Healthy Chains", weight: 35, score: 92, contribution: 32.2 },
      { metric: "Pattern Pass Rate", weight: 20, score: 81, contribution: 16.2 },
      { metric: "Coverage", weight: 20, score: 96.8, contribution: 19.4 },
      { metric: "Diagnosis Confidence", weight: 15, score: 91, contribution: 13.6 },
      { metric: "Test Stability", weight: 10, score: 65, contribution: 6.5 },
    ],
  };
}
