"use client";

import { BrainCircuit } from "lucide-react";
import { RecommendationActionButtons } from "@/components/platform/RecommendationActionButtons";
import { TrendLineChart } from "@/components/scan-chain/charts/LineCharts";
import { DistributionPie } from "@/components/scan-chain/charts/PieCharts";
import { ChartCard } from "@/components/scan-chain/ChartCard";
import { DataTable } from "@/components/scan-chain/DataTable";
import { AgentActionBar } from "@/components/recommendation/AgentActionBar";
import { AgentSummaryCard } from "@/components/recommendation/AgentSummaryCard";
import { AgentTabHeader } from "@/components/recommendation/AgentTabHeader";
import { PriorityBadge, StatusBadge } from "@/components/recommendation/Badges";
import { CenterKPIGrid } from "@/components/recommendation/CenterKPIGrid";
import { useFilteredRecommendationKPIs } from "@/hooks/useFilteredRecommendationKPIs";
import {
  patternAgentKPIs,
  patternAgentSummary,
  patternClusterData,
  patternCoverageTrend,
  patternRecDistribution,
  patternRecRows,
  powerSavingTrend,
} from "@/lib/recommendationData";

export function PatternAgentTab() {
  const kpis = useFilteredRecommendationKPIs(patternAgentKPIs);

  return (
    <div className="dashboard-content">
      <AgentTabHeader
        icon={BrainCircuit}
        title="Pattern Recommendation Agent"
        description="AI engine for ATPG pattern optimization, redundancy removal, pattern ordering, coverage improvement and low-power optimization."
      />

      <CenterKPIGrid data={kpis} />

      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Recommendation Distribution" subtitle="By optimization category">
          <DistributionPie data={patternRecDistribution} />
        </ChartCard>
        <ChartCard title="Coverage Improvement Trend" subtitle="Current vs. projected coverage">
          <TrendLineChart
            data={patternCoverageTrend}
            lines={[
              { key: "value", color: "#64748B", name: "Current" },
              { key: "value2", color: "#22C55E", name: "Projected" },
            ]}
          />
        </ChartCard>
        <ChartCard title="Power Saving Trend" subtitle="Baseline vs. optimized power">
          <TrendLineChart
            data={powerSavingTrend}
            lines={[
              { key: "value", color: "#64748B", name: "Current" },
              { key: "value2", color: "#06B6D4", name: "Optimized" },
            ]}
          />
        </ChartCard>
        <ChartCard title="Pattern Cluster Analysis" subtitle="AI similarity cluster distribution">
          <DistributionPie data={patternClusterData} />
        </ChartCard>
      </div>

      <DataTable
        title="Pattern Recommendation Table"
        subtitle="ATPG pattern optimization recommendations"
        data={patternRecRows}
        rowKey="recommendationId"
        pageSize={5}
        searchKeys={["recommendationId", "patternId", "recommendation", "status"]}
        searchPlaceholder="Search pattern recommendations..."
        columns={[
          {
            key: "recommendationId",
            label: "Recommendation ID",
            render: (row) => (
              <span className="font-mono text-xs font-medium text-white">
                {row.recommendationId}
              </span>
            ),
          },
          {
            key: "patternId",
            label: "Pattern ID",
            render: (row) => (
              <span className="font-mono text-xs text-slate-300">{row.patternId}</span>
            ),
          },
          { key: "recommendation", label: "Recommendation" },
          {
            key: "priority",
            label: "Priority",
            render: (row) => <PriorityBadge priority={row.priority} />,
          },
          {
            key: "confidence",
            label: "Confidence",
            render: (row) => `${row.confidence}%`,
          },
          { key: "coverageGain", label: "Coverage Gain" },
          { key: "powerSaving", label: "Power Saving" },
          {
            key: "status",
            label: "Status",
            render: (row) => <StatusBadge status={row.status} />,
          },
          {
            key: "action",
            label: "Action",
            sortable: false,
            render: (row) => <RecommendationActionButtons id={row.recommendationId} />,
          },
        ]}
      />

      <AgentSummaryCard data={patternAgentSummary} />
      <AgentActionBar />
    </div>
  );
}
