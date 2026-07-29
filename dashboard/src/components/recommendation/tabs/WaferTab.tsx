"use client";

import { TabLiveShell } from "@/components/platform/TabLiveShell";
import { RecommendationActionButtons } from "@/components/platform/RecommendationActionButtons";
import { VerticalBarChart } from "@/components/scan-chain/charts/BarCharts";
import { TrendLineChart } from "@/components/scan-chain/charts/LineCharts";
import { DistributionPie } from "@/components/scan-chain/charts/PieCharts";
import { ChartCard } from "@/components/scan-chain/ChartCard";
import { DataTable } from "@/components/scan-chain/DataTable";
import { PriorityBadge } from "@/components/recommendation/Badges";
import { KPIGrid } from "@/components/recommendation/KPICard";
import { WaferRecHeatmap } from "@/components/recommendation/WaferRecHeatmap";
import { useFilteredRecommendationData } from "@/hooks/useRecommendationData";

export function WaferTab() {
  const liveData = useFilteredRecommendationData();
  const {waferKPIs, waferRecommendations, waferYieldTrend } = liveData;

  return (
    <TabLiveShell module="recommendation-analysis" hookResult={liveData}>
      <div className="dashboard-content">
      <KPIGrid data={waferKPIs} />
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Wafer Yield Trend" subtitle="Yield improvement trajectory">
          <TrendLineChart data={waferYieldTrend} lines={[{ key: "value", color: "#22C55E", name: "Yield %" }]} />
        </ChartCard>
        <ChartCard title="Defect Density" subtitle="Defect density by zone">
          <VerticalBarChart data={[{ label: "Zone A", value: 82 }, { label: "Zone B", value: 68 }, { label: "Zone C", value: 74 }, { label: "Zone D", value: 58 }]} color="#EF4444" />
        </ChartCard>
        <ChartCard title="Yield Distribution" subtitle="Bin yield distribution">
          <DistributionPie data={[{ name: "Bin 1", value: 72, color: "#22C55E" }, { name: "Bin 2", value: 18, color: "#EAB308" }, { name: "Bin 3", value: 10, color: "#EF4444" }]} />
        </ChartCard>
      </div>
      <WaferRecHeatmap />
      <DataTable
        title="Wafer Recommendations"
        subtitle="Yield improvement, defect hotspots, wafer retest, and bin optimization"
        data={waferRecommendations}
        rowKey="id"
        searchKeys={["id", "lotId", "waferId", "recommendation"]}
        searchPlaceholder="Search wafer recommendations..."
        columns={[
          { key: "id", label: "Recommendation ID", render: (row) => <span className="font-mono text-xs text-white">{row.id}</span> },
          { key: "lotId", label: "Lot ID" },
          { key: "waferId", label: "Wafer ID" },
          { key: "recommendation", label: "Recommendation" },
          { key: "priority", label: "Priority", render: (row) => <PriorityBadge priority={row.priority} /> },
          { key: "confidence", label: "Confidence", render: (row) => `${row.confidence}%` },
          { key: "expectedYield", label: "Expected Yield" },
          { key: "action", label: "Action", sortable: false, render: (row) => <RecommendationActionButtons id={row.id} /> },
        ]}
      />
      </div>
    </TabLiveShell>
  );
}
