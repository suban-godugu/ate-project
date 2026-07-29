"use client";

import { TabLiveShell } from "@/components/platform/TabLiveShell";
import { VerticalBarChart } from "@/components/scan-chain/charts/BarCharts";
import { TrendLineChart } from "@/components/scan-chain/charts/LineCharts";
import { ChartCard } from "@/components/scan-chain/ChartCard";
import { DataTable } from "@/components/scan-chain/DataTable";
import { KPIGrid } from "@/components/cost-intelligence/KPICard";
import { useFilteredCostIntelligenceData } from "@/hooks/useCostIntelligenceData";

export function ScanChainCostTab() {
  const liveData = useFilteredCostIntelligenceData();
  const { patternCostTrend, scanChainCostRows, scanChainKPIs } = liveData;

  const patternBars = scanChainCostRows
    .map((row) => ({
      label: row.patternId,
      value: parseFloat(String(row.cost).replace(/[$,]/g, "")) / 1000 || 0,
    }))
    .filter((b) => b.value > 0)
    .slice(0, 6);

  const runtimeBars = scanChainCostRows
    .map((row) => ({
      label: row.patternId,
      value: parseFloat(String(row.executionTime).replace(/[^\d.]/g, "")) || 0,
    }))
    .filter((b) => b.value > 0)
    .slice(0, 6);

  const chainBars = scanChainCostRows
    .reduce<{ label: string; value: number }[]>((acc, row) => {
      const existing = acc.find((a) => a.label === row.scanChain);
      const cost = parseFloat(String(row.cost).replace(/[$,]/g, "")) / 1000 || 0;
      if (existing) existing.value += cost;
      else acc.push({ label: row.scanChain, value: cost });
      return acc;
    }, [])
    .slice(0, 6);

  return (
    <TabLiveShell module="cost-intelligence" hookResult={liveData}>
      <div className="dashboard-content">
      <KPIGrid data={scanChainKPIs} />
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Pattern Cost Trend" subtitle="Weekly pattern execution cost ($K)">
          <TrendLineChart data={patternCostTrend} lines={[{ key: "value", color: "#7C3AED", name: "Pattern Cost" }]} />
        </ChartCard>
        <ChartCard title="Cost Per Pattern" subtitle="Top pattern costs ($K)">
          <VerticalBarChart data={patternBars.length ? patternBars : [{ label: "—", value: 0 }]} color="#7C3AED" />
        </ChartCard>
        <ChartCard title="Top Expensive Scan Chains" subtitle="Cost by scan chain ($K)">
          <VerticalBarChart data={chainBars.length ? chainBars : [{ label: "—", value: 0 }]} color="#F97316" />
        </ChartCard>
        <ChartCard title="Pattern Runtime" subtitle="Execution time by pattern (min)">
          <VerticalBarChart
            data={runtimeBars.length ? runtimeBars : [{ label: "—", value: 0 }]}
            color="#06B6D4"
          />
        </ChartCard>
      </div>
      <DataTable
        title="Scan Chain Cost Table"
        subtitle="Pattern execution costs and optimization recommendations"
        data={scanChainCostRows}
        rowKey="patternId"
        searchKeys={["patternId", "scanChain", "recommendation"]}
        searchPlaceholder="Search patterns, scan chains..."
        columns={[
          { key: "patternId", label: "Pattern ID", render: (row) => <span className="font-mono text-xs text-white">{row.patternId}</span> },
          { key: "scanChain", label: "Scan Chain" },
          { key: "executionTime", label: "Execution Time" },
          { key: "cost", label: "Cost" },
          { key: "recommendation", label: "Recommendation" },
          { key: "expectedSavings", label: "Expected Savings", render: (row) => <span className="text-emerald-400">{row.expectedSavings}</span> },
        ]}
      />
      </div>
    </TabLiveShell>
  );
}
