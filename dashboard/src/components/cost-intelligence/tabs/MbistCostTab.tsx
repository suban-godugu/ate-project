"use client";

import { TabLiveShell } from "@/components/platform/TabLiveShell";
import { VerticalBarChart } from "@/components/scan-chain/charts/BarCharts";
import { TrendLineChart } from "@/components/scan-chain/charts/LineCharts";
import { DistributionPie } from "@/components/scan-chain/charts/PieCharts";
import { ChartCard } from "@/components/scan-chain/ChartCard";
import { DataTable } from "@/components/scan-chain/DataTable";
import { KPIGrid } from "@/components/cost-intelligence/KPICard";
import { useFilteredCostIntelligenceData } from "@/hooks/useCostIntelligenceData";

export function MbistCostTab() {
  const liveData = useFilteredCostIntelligenceData();
  const {mbistCostRows, mbistKPIs, memoryCostTrend } = liveData;

  return (
    <TabLiveShell module="cost-intelligence" hookResult={liveData}>
      <div className="dashboard-content">
      <KPIGrid data={mbistKPIs} />
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Memory Cost Trend" subtitle="Weekly MBIST cost ($K)">
          <TrendLineChart data={memoryCostTrend} lines={[{ key: "value", color: "#06B6D4", name: "MBIST Cost" }]} />
        </ChartCard>
        <ChartCard title="Bank Cost" subtitle="Cost by memory bank ($K)">
          <VerticalBarChart data={[{ label: "Bank-0", value: 8.4 }, { label: "Bank-1", value: 7.8 }, { label: "Bank-2", value: 9.2 }, { label: "Bank-4", value: 6.6 }]} color="#06B6D4" />
        </ChartCard>
        <ChartCard title="Repair Cost" subtitle="Repair type distribution">
          <DistributionPie data={[{ name: "FIB Repair", value: 38, color: "#7C3AED" }, { name: "Redundancy", value: 32, color: "#06B6D4" }, { name: "Soft Repair", value: 30, color: "#F97316" }]} />
        </ChartCard>
        <ChartCard title="Memory Runtime" subtitle="Runtime cost by bank ($K)">
          <VerticalBarChart data={[{ label: "Bank-0", value: 3.8 }, { label: "Bank-1", value: 3.4 }, { label: "Bank-2", value: 4.2 }, { label: "Bank-4", value: 2.8 }]} color="#22C55E" />
        </ChartCard>
      </div>
      <DataTable
        title="MBIST Cost Table"
        subtitle="Memory test and repair costs with recommendations"
        data={mbistCostRows}
        rowKey="memory"
        searchKeys={["memory", "bank", "recommendation"]}
        searchPlaceholder="Search memories, banks..."
        columns={[
          { key: "memory", label: "Memory" },
          { key: "bank", label: "Bank" },
          { key: "cost", label: "Cost" },
          { key: "repairCost", label: "Repair Cost" },
          { key: "recommendation", label: "Recommendation" },
        ]}
      />
      </div>
    </TabLiveShell>
  );
}
