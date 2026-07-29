"use client";

import { TabLiveShell } from "@/components/platform/TabLiveShell";
import { RecommendationActionButtons } from "@/components/platform/RecommendationActionButtons";
import { VerticalBarChart } from "@/components/scan-chain/charts/BarCharts";
import { TrendLineChart } from "@/components/scan-chain/charts/LineCharts";
import { ChartCard } from "@/components/scan-chain/ChartCard";
import { DataTable } from "@/components/scan-chain/DataTable";
import { PriorityBadge } from "@/components/recommendation/Badges";
import { KPIGrid } from "@/components/recommendation/KPICard";
import { useFilteredRecommendationData } from "@/hooks/useRecommendationData";

export function ScanChainTab() {
  const liveData = useFilteredRecommendationData();
  const { chainHealthTrend, scanChainKPIs, scanChainRecommendations, scanFailureTrend } =liveData;

  return (
    <TabLiveShell module="recommendation-analysis" hookResult={liveData}>
      <div className="dashboard-content">
      <KPIGrid data={scanChainKPIs} />
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Scan Failure Trend" subtitle="Failures vs. critical chains">
          <TrendLineChart data={scanFailureTrend} lines={[{ key: "value", color: "#EF4444", name: "Failures" }, { key: "value2", color: "#F97316", name: "Critical" }]} />
        </ChartCard>
        <ChartCard title="Chain Health" subtitle="Health distribution">
          <VerticalBarChart data={chainHealthTrend} color="#22C55E" />
        </ChartCard>
        <ChartCard title="Pattern Optimization" subtitle="Optimization opportunity score">
          <VerticalBarChart data={[{ label: "PAT-042", value: 92 }, { label: "PAT-118", value: 78 }, { label: "PAT-007", value: 86 }, { label: "PAT-056", value: 74 }]} color="#7C3AED" />
        </ChartCard>
        <ChartCard title="Chain Priority" subtitle="Priority-ranked scan chains">
          <VerticalBarChart data={[{ label: "SC-4821", value: 98 }, { label: "SC-3156", value: 86 }, { label: "SC-7892", value: 82 }, { label: "SC-2441", value: 74 }]} color="#F97316" />
        </ChartCard>
      </div>
      <DataTable
        title="Scan Chain Recommendations"
        subtitle="Pattern optimization, chain diagnosis, and compression improvements"
        data={scanChainRecommendations}
        rowKey="id"
        searchKeys={["id", "scanChain", "pattern", "recommendation"]}
        searchPlaceholder="Search scan recommendations..."
        columns={[
          { key: "id", label: "Recommendation ID", render: (row) => <span className="font-mono text-xs text-white">{row.id}</span> },
          { key: "scanChain", label: "Scan Chain" },
          { key: "pattern", label: "Pattern" },
          { key: "recommendation", label: "Recommendation" },
          { key: "priority", label: "Priority", render: (row) => <PriorityBadge priority={row.priority} /> },
          { key: "confidence", label: "Confidence", render: (row) => `${row.confidence}%` },
          { key: "expectedResult", label: "Expected Result" },
          { key: "action", label: "Action", sortable: false, render: (row) => <RecommendationActionButtons id={row.id} /> },
        ]}
      />
      </div>
    </TabLiveShell>
  );
}
