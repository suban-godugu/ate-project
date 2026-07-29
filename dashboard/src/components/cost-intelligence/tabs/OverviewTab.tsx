"use client";

import { TabLiveShell } from "@/components/platform/TabLiveShell";
import { TrendLineChart } from "@/components/scan-chain/charts/LineCharts";
import { DonutChart } from "@/components/scan-chain/charts/PieCharts";
import { ChartCard } from "@/components/scan-chain/ChartCard";
import { DataTable } from "@/components/scan-chain/DataTable";
import { ModuleHorizontalBarChart, StackedCostBarChart } from "@/components/cost-intelligence/CostCharts";
import { AICostSummaryCard, EnterpriseCostSummaryPanel } from "@/components/cost-intelligence/CostPanels";
import { KPIGrid } from "@/components/cost-intelligence/KPICard";
import { useFilteredCostIntelligenceData } from "@/hooks/useCostIntelligenceData";

export function OverviewTab() {
  const liveData = useFilteredCostIntelligenceData();
  const {aiCostSummary,
    costBreakdown,
    costContribution,
    costDistribution,
    enterpriseCostSummary,
    monthlyCostTrend,
    overviewKPIs,
    productCostRows,
  } = liveData;

  return (
    <TabLiveShell module="cost-intelligence" hookResult={liveData}>
      <div className="dashboard-content">
      <KPIGrid data={overviewKPIs} />
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Cost Contribution" subtitle="Percentage by analysis module">
          <DonutChart
            data={costContribution}
            centerLabel="Total"
            centerValue={overviewKPIs[0]?.value ?? "—"}
          />
          <div className="mt-4 flex flex-wrap gap-3">
            {costContribution.map((s) => (
              <div key={s.name} className="flex items-center gap-1.5 text-xs text-slate-400">
                <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: s.color }} />
                {s.name}: {s.value}%
              </div>
            ))}
          </div>
        </ChartCard>
        <ChartCard title="Cost Breakdown" subtitle="Total cost by module ($K)">
          <ModuleHorizontalBarChart data={costBreakdown} />
        </ChartCard>
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Monthly Cost Trend" subtitle="Last 6 months ($K)">
          <TrendLineChart data={monthlyCostTrend} lines={[{ key: "value", color: "#7C3AED", name: "Total Cost" }]} />
        </ChartCard>
        <ChartCard title="Cost Distribution" subtitle="Stacked cost categories ($K)">
          <StackedCostBarChart data={costDistribution} />
        </ChartCard>
      </div>
      <DataTable
        title="Cost by Product"
        subtitle="Product-level cost analysis with estimated savings"
        data={productCostRows}
        rowKey="lot"
        searchKeys={["product", "lot", "wafer"]}
        searchPlaceholder="Search products, lots, wafers..."
        pageSize={5}
        columns={[
          { key: "product", label: "Product" },
          { key: "lot", label: "Lot" },
          { key: "wafer", label: "Wafer" },
          { key: "totalCost", label: "Total Cost" },
          { key: "costPerDie", label: "Cost Per Die" },
          { key: "yield", label: "Yield" },
          { key: "estimatedSavings", label: "Estimated Savings", render: (row) => <span className="text-emerald-400">{row.estimatedSavings}</span> },
        ]}
      />
      <AICostSummaryCard data={aiCostSummary} />
      <EnterpriseCostSummaryPanel data={enterpriseCostSummary} />
      </div>
    </TabLiveShell>
  );
}
