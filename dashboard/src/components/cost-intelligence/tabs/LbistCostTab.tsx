"use client";

import { TabLiveShell } from "@/components/platform/TabLiveShell";
import { VerticalBarChart } from "@/components/scan-chain/charts/BarCharts";
import { TrendLineChart } from "@/components/scan-chain/charts/LineCharts";
import { ChartCard } from "@/components/scan-chain/ChartCard";
import { DataTable } from "@/components/scan-chain/DataTable";
import { KPIGrid } from "@/components/cost-intelligence/KPICard";
import { useFilteredCostIntelligenceData } from "@/hooks/useCostIntelligenceData";

export function LbistCostTab() {
  const liveData = useFilteredCostIntelligenceData();
  const {lbistCostRows, lbistKPIs, logicCostTrend } = liveData;

  return (
    <TabLiveShell module="cost-intelligence" hookResult={liveData}>
      <div className="dashboard-content">
      <KPIGrid data={lbistKPIs} />
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Logic Cost Trend" subtitle="Weekly LBIST cost ($K)">
          <TrendLineChart data={logicCostTrend} lines={[{ key: "value", color: "#F97316", name: "Logic Cost" }]} />
        </ChartCard>
        <ChartCard title="Coverage Cost" subtitle="Coverage-related cost ($K)">
          <VerticalBarChart data={[{ label: "GPU", value: 8.2 }, { label: "NOC", value: 6.8 }, { label: "CPU", value: 7.4 }, { label: "DSP", value: 5.2 }]} color="#F97316" />
        </ChartCard>
        <ChartCard title="Signature Runtime" subtitle="MISR runtime cost (min)">
          <VerticalBarChart data={[{ label: "GPU", value: 18 }, { label: "NOC", value: 14 }, { label: "CPU", value: 16 }, { label: "DSP", value: 10 }]} color="#7C3AED" />
        </ChartCard>
        <ChartCard title="Logic Module Cost" subtitle="Cost by logic block ($K)">
          <VerticalBarChart data={[{ label: "LB-GPU", value: 14.2 }, { label: "LB-NOC", value: 11.8 }, { label: "LB-CPU", value: 12.4 }, { label: "LB-DSP", value: 8.6 }]} color="#06B6D4" />
        </ChartCard>
      </div>
      <DataTable
        title="LBIST Cost Table"
        subtitle="Logic test costs and optimization recommendations"
        data={lbistCostRows}
        rowKey="logicBlock"
        searchKeys={["logicBlock", "recommendation"]}
        searchPlaceholder="Search logic blocks..."
        columns={[
          { key: "logicBlock", label: "Logic Block" },
          { key: "runtime", label: "Runtime" },
          { key: "cost", label: "Cost" },
          { key: "recommendation", label: "Recommendation" },
        ]}
      />
      </div>
    </TabLiveShell>
  );
}
