"use client";

import { TabLiveShell } from "@/components/platform/TabLiveShell";
import { VerticalBarChart } from "@/components/scan-chain/charts/BarCharts";
import { TrendLineChart } from "@/components/scan-chain/charts/LineCharts";
import { ChartCard } from "@/components/scan-chain/ChartCard";
import { KPIGrid } from "@/components/lbist/KPICard";
import { LBISTHeatmap } from "@/components/lbist/LBISTHeatmap";
import { useFilteredLbistData } from "@/hooks/useLbistData";

export function CoverageAnalysisTab() {
  const liveData = useFilteredLbistData();
  const {coverageByBlock,
    coverageKPIs,
    coverageTrend,
    faultDetectionRate,
    patternEfficiency,
  } = liveData;

  return (
    <TabLiveShell module="lbist" hookResult={liveData}>
      <div className="dashboard-content">
      <KPIGrid data={coverageKPIs} />
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Coverage Trend" subtitle="Overall vs. target coverage">
          <TrendLineChart data={coverageTrend} lines={[{ key: "value", color: "#7C3AED", name: "Coverage %" }, { key: "value2", color: "#06B6D4", name: "Target %" }]} />
        </ChartCard>
        <ChartCard title="Coverage by Logic Block" subtitle="Block-level coverage breakdown">
          <VerticalBarChart data={coverageByBlock} color="#22C55E" />
        </ChartCard>
        <ChartCard title="Pattern Efficiency" subtitle="LBIST pattern efficiency scores">
          <VerticalBarChart data={patternEfficiency} color="#7C3AED" />
        </ChartCard>
        <ChartCard title="Fault Detection Rate" subtitle="Detection rate over time">
          <TrendLineChart data={faultDetectionRate} lines={[{ key: "value", color: "#F97316", name: "Detection Rate %" }]} />
        </ChartCard>
      </div>
      <LBISTHeatmap />
      </div>
    </TabLiveShell>
  );
}
