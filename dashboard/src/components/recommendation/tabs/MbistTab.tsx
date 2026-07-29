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
import { useFilteredRecommendationData } from "@/hooks/useRecommendationData";

export function MbistTab() {
  const liveData = useFilteredRecommendationData();
  const {mbistKPIs, mbistRecommendations, memoryFailureTrend } = liveData;

  return (
    <TabLiveShell module="recommendation-analysis" hookResult={liveData}>
      <div className="dashboard-content">
      <KPIGrid data={mbistKPIs} />
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Memory Failure Trend" subtitle="Weekly failure count">
          <TrendLineChart data={memoryFailureTrend} lines={[{ key: "value", color: "#EF4444", name: "Failures" }]} />
        </ChartCard>
        <ChartCard title="Memory Health" subtitle="Health score by bank">
          <VerticalBarChart data={[{ label: "Bank-0", value: 88 }, { label: "Bank-1", value: 92 }, { label: "Bank-2", value: 86 }, { label: "Bank-4", value: 94 }]} color="#22C55E" />
        </ChartCard>
        <ChartCard title="Repair Distribution" subtitle="Repair type breakdown">
          <DistributionPie data={[{ name: "FIB Repair", value: 32, color: "#7C3AED" }, { name: "Redundancy", value: 28, color: "#06B6D4" }, { name: "Timing Fix", value: 24, color: "#F97316" }, { name: "Other", value: 16, color: "#64748B" }]} />
        </ChartCard>
        <ChartCard title="Bank Analysis" subtitle="Recommendations by bank">
          <VerticalBarChart data={[{ label: "Bank-0", value: 12 }, { label: "Bank-1", value: 8 }, { label: "Bank-2", value: 10 }, { label: "Bank-4", value: 6 }]} color="#06B6D4" />
        </ChartCard>
      </div>
      <DataTable
        title="MBIST Recommendations"
        subtitle="Memory repair, redundancy allocation, and coverage improvement"
        data={mbistRecommendations}
        rowKey="id"
        searchKeys={["id", "memory", "bank", "recommendation"]}
        searchPlaceholder="Search MBIST recommendations..."
        columns={[
          { key: "id", label: "Recommendation ID", render: (row) => <span className="font-mono text-xs text-white">{row.id}</span> },
          { key: "memory", label: "Memory" },
          { key: "bank", label: "Bank" },
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
