"use client";

import { TabLiveShell } from "@/components/platform/TabLiveShell";
import { VerticalBarChart } from "@/components/scan-chain/charts/BarCharts";
import { TrendLineChart } from "@/components/scan-chain/charts/LineCharts";
import { DistributionPie } from "@/components/scan-chain/charts/PieCharts";
import { ChartCard } from "@/components/scan-chain/ChartCard";
import { DataTable } from "@/components/scan-chain/DataTable";
import { KPIGrid } from "@/components/cost-intelligence/KPICard";
import { WaferCostHeatmap } from "@/components/cost-intelligence/WaferCostHeatmap";
import { useFilteredCostIntelligenceData } from "@/hooks/useCostIntelligenceData";

export function WaferCostTab() {
  const liveData = useFilteredCostIntelligenceData();
  const { waferCostRows, waferCostTrend, waferKPIs, defectDensityCost, yieldBinDistribution } = liveData;

  const defectBars = (defectDensityCost ?? []).map((item) => ({
    label: String(item.label),
    value: Number(item.value) || 0,
  }));

  const yieldPie = (yieldBinDistribution ?? []).map((item) => ({
    name: String(item.name),
    value: Number(item.value) || 0,
    color: String(item.color ?? "#94A3B8"),
  }));

  return (
    <TabLiveShell module="cost-intelligence" hookResult={liveData}>
      <div className="dashboard-content">
      <KPIGrid data={waferKPIs} />
      <WaferCostHeatmap />
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Yield Cost" subtitle="Yield loss cost trend ($K)">
          <TrendLineChart data={waferCostTrend} lines={[{ key: "value", color: "#22C55E", name: "Wafer Cost" }]} />
        </ChartCard>
        <ChartCard title="Defect Density Cost" subtitle="Cost by defect zone ($K)">
          <VerticalBarChart data={defectBars.length ? defectBars : [{ label: "—", value: 0 }]} color="#EF4444" />
        </ChartCard>
        <ChartCard title="Wafer Trend" subtitle="Weekly wafer test cost ($K)">
          <TrendLineChart data={waferCostTrend} lines={[{ key: "value", color: "#7C3AED", name: "Cost" }]} />
        </ChartCard>
        <ChartCard title="Yield Distribution" subtitle="Bin cost distribution">
          <DistributionPie data={yieldPie.length ? yieldPie : [{ name: "—", value: 0, color: "#64748B" }]} />
        </ChartCard>
      </div>
      <DataTable
        title="Wafer Cost Table"
        subtitle="Lot and wafer-level costs with recommendations"
        data={waferCostRows}
        rowKey="lot"
        searchKeys={["lot", "wafer", "recommendation"]}
        searchPlaceholder="Search lots, wafers..."
        columns={[
          { key: "lot", label: "Lot" },
          { key: "wafer", label: "Wafer" },
          { key: "yield", label: "Yield" },
          { key: "cost", label: "Cost" },
          { key: "recommendation", label: "Recommendation" },
        ]}
      />
      </div>
    </TabLiveShell>
  );
}
