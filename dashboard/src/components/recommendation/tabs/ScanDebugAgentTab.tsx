"use client";

import { Bug } from "lucide-react";
import { RecommendationActionButtons } from "@/components/platform/RecommendationActionButtons";
import { VerticalBarChart } from "@/components/scan-chain/charts/BarCharts";
import { TrendLineChart } from "@/components/scan-chain/charts/LineCharts";
import { DonutChart } from "@/components/scan-chain/charts/PieCharts";
import { ChartCard } from "@/components/scan-chain/ChartCard";
import { DataTable } from "@/components/scan-chain/DataTable";
import { AgentActionBar } from "@/components/recommendation/AgentActionBar";
import { AgentSummaryCard } from "@/components/recommendation/AgentSummaryCard";
import { AgentTabHeader } from "@/components/recommendation/AgentTabHeader";
import { AgentWorkflowDiagram } from "@/components/recommendation/AgentWorkflowDiagram";
import { PriorityBadge, StatusBadge } from "@/components/recommendation/Badges";
import { SectionedKPIGrid } from "@/components/recommendation/SectionedKPIGrid";
import { useFilteredKPISections } from "@/hooks/useFilteredRecommendationKPIs";
import {
  debugRecommendationPriority,
  failureRootCauseDistribution,
  scanDebugAgentSummary,
  scanDebugKPISections,
  scanDebugRecRows,
  scanDebugRecommendationTrend,
  scanDebugWorkflowSteps,
} from "@/lib/recommendationData";

export function ScanDebugAgentTab() {
  const kpiSections = useFilteredKPISections(scanDebugKPISections);

  return (
    <div className="dashboard-content">
      <AgentTabHeader
        icon={Bug}
        title="Scan Debug Recommendation Agent"
        description="AI-powered failure diagnosis and debug recommendations for Scan Chain testing."
      />

      <SectionedKPIGrid sections={kpiSections} variant="section" />

      <div className="grid gap-6 lg:grid-cols-3">
        <ChartCard title="Failure Root Cause Distribution" subtitle="By debug category">
          <DonutChart
            data={failureRootCauseDistribution}
            centerLabel="Root Causes"
            centerValue={failureRootCauseDistribution.reduce((s, d) => s + d.value, 0)}
          />
        </ChartCard>
        <ChartCard title="Debug Recommendation Priority" subtitle="By priority level">
          <VerticalBarChart data={debugRecommendationPriority} color="#7C3AED" />
        </ChartCard>
        <ChartCard title="Recommendation Trend" subtitle="Last 30 days">
          <TrendLineChart
            data={scanDebugRecommendationTrend}
            lines={[{ key: "value", color: "#7C3AED", name: "Recommendations" }]}
          />
        </ChartCard>
      </div>

      <DataTable
        title="Top Scan Debug Recommendations"
        subtitle="Priority debug actions ranked by AI confidence and impact"
        data={scanDebugRecRows}
        rowKey="recommendationId"
        pageSize={6}
        searchKeys={[
          "recommendationId",
          "category",
          "scanChain",
          "rootCause",
          "recommendation",
          "engineer",
        ]}
        searchPlaceholder="Search debug recommendations..."
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
          { key: "category", label: "Category" },
          { key: "scanChain", label: "Scan Chain" },
          { key: "rootCause", label: "Root Cause" },
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
          { key: "engineer", label: "Engineer" },
          {
            key: "status",
            label: "Status",
            render: (row) => <StatusBadge status={row.status} />,
          },
          { key: "expectedImpact", label: "Expected Impact" },
          {
            key: "action",
            label: "Action",
            sortable: false,
            render: (row) => <RecommendationActionButtons id={row.recommendationId} />,
          },
        ]}
      />

      <AgentSummaryCard data={scanDebugAgentSummary} />

      <AgentWorkflowDiagram
        steps={scanDebugWorkflowSteps}
        title="Debug Workflow"
        subtitle="From failure logs through validation"
      />

      <AgentActionBar variant="scan-debug" />
    </div>
  );
}
