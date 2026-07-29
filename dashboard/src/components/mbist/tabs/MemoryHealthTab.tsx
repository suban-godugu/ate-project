"use client";

import { TabLiveShell } from "@/components/platform/TabLiveShell";
import { VerticalBarChart } from "@/components/scan-chain/charts/BarCharts";
import { TrendLineChart } from "@/components/scan-chain/charts/LineCharts";
import { ChartCard } from "@/components/scan-chain/ChartCard";
import { KPIGrid } from "@/components/mbist/KPICard";
import { useFilteredMbistData } from "@/hooks/useMbistData";

export function MemoryHealthTab() {
  const liveData = useFilteredMbistData();
  const {accessDistribution,
    memoryDensity,
    memoryHealthKPIs,
    temperatureTrend,
    utilizationTrend,
  } = liveData;

  return (
    <TabLiveShell module="mbist" hookResult={liveData}>
      <div className="dashboard-content">
      <KPIGrid data={memoryHealthKPIs} />
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Memory Utilization Trend" subtitle="Utilization vs. capacity over time">
          <TrendLineChart data={utilizationTrend} lines={[{ key: "value", color: "#7C3AED", name: "Utilization %" }, { key: "value2", color: "#06B6D4", name: "Capacity %" }]} />
        </ChartCard>
        <ChartCard title="Memory Temperature" subtitle="Average die temperature during MBIST">
          <TrendLineChart data={temperatureTrend} lines={[{ key: "value", color: "#F97316", name: "Temp (°C)" }]} />
        </ChartCard>
        <ChartCard title="Memory Access Distribution" subtitle="Access pattern breakdown">
          <VerticalBarChart data={accessDistribution} color="#22C55E" />
        </ChartCard>
        <ChartCard title="Memory Density" subtitle="Instance density by zone">
          <VerticalBarChart data={memoryDensity} color="#7C3AED" />
        </ChartCard>
      </div>
      </div>
    </TabLiveShell>
  );
}
