"use client";

import { TabLiveShell } from "@/components/platform/TabLiveShell";
import { ArrowUpRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { VerticalBarChart } from "@/components/scan-chain/charts/BarCharts";
import { TrendLineChart } from "@/components/scan-chain/charts/LineCharts";
import { DonutChart } from "@/components/scan-chain/charts/PieCharts";
import { ChartCard } from "@/components/scan-chain/ChartCard";
import { DataTable } from "@/components/scan-chain/DataTable";
import { AIExecutiveSummaryCard } from "@/components/recommendation/AIExecutiveSummaryCard";
import { ModuleBadge, PriorityBadge, StatusBadge } from "@/components/recommendation/Badges";
import { recommendationRlColumns } from "@/components/recommendation/RecommendationRlColumns";
import { BottomAISummaryPanel, RecommendationEnginePanel, WorkflowPanel } from "@/components/recommendation/EnginePanels";
import { KPIGrid } from "@/components/recommendation/KPICard";
import { useFilteredRecommendationData } from "@/hooks/useRecommendationData";

export function OverviewTab() {
  const liveData = useFilteredRecommendationData();
  const {aiExecutiveSummary,
    bottomAISummary,
    overviewKPIs,
    priorityDistribution,
    recommendationTrend,
    sourceDistribution,
    unifiedRecommendations,
  } = liveData;

  return (
    <TabLiveShell module="recommendation-analysis" hookResult={liveData}>
      <div className="dashboard-content">
      <KPIGrid data={overviewKPIs} />
      <div className="grid gap-6 lg:grid-cols-3">
        <ChartCard title="Recommendation Sources" subtitle="By analysis module" className="lg:col-span-1">
          <DonutChart data={sourceDistribution} centerLabel="Total" centerValue="186" />
          <div className="mt-4 flex flex-wrap gap-3">
            {sourceDistribution.map((s) => (
              <div key={s.name} className="flex items-center gap-1.5 text-xs text-slate-400">
                <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: s.color }} />
                {s.name}: {s.value}
              </div>
            ))}
          </div>
        </ChartCard>
        <ChartCard title="Recommendation Priority" subtitle="By priority level" className="lg:col-span-1">
          <VerticalBarChart data={priorityDistribution} color="#7C3AED" />
        </ChartCard>
        <ChartCard title="Recommendation Trend" subtitle="Last 30 days" className="lg:col-span-1">
          <TrendLineChart data={recommendationTrend} lines={[{ key: "value", color: "#7C3AED", name: "Recommendations" }]} />
        </ChartCard>
      </div>
      <DataTable
        title="Unified Recommendation Table"
        subtitle="All recommendations consolidated from Scan Chain, MBIST, LBIST, and Wafer Analysis"
        data={unifiedRecommendations}
        rowKey="id"
        searchKeys={["id", "sourceModule", "category", "assignedEngineer"]}
        searchPlaceholder="Search recommendations..."
        pageSize={5}
        columns={[
          { key: "id", label: "Recommendation ID", render: (row) => <span className="font-mono text-xs text-white">{row.id}</span> },
          { key: "sourceModule", label: "Source Module", render: (row) => <ModuleBadge module={row.sourceModule} /> },
          { key: "category", label: "Category" },
          { key: "priority", label: "Priority", render: (row) => <PriorityBadge priority={row.priority} /> },
          { key: "confidence", label: "Confidence", render: (row) => `${row.confidence}%` },
          ...recommendationRlColumns<typeof unifiedRecommendations[number]>(),
          { key: "estimatedImpact", label: "Estimated Impact" },
          { key: "status", label: "Status", render: (row) => <StatusBadge status={row.status} /> },
          { key: "assignedEngineer", label: "Assigned Engineer" },
          { key: "action", label: "Action", sortable: false, render: () => <Button variant="ghost" size="sm" className="h-7 text-xs text-[#7C3AED]">View<ArrowUpRight className="ml-1 h-3 w-3" /></Button> },
        ]}
      />
      <AIExecutiveSummaryCard data={aiExecutiveSummary} />
      <RecommendationEnginePanel />
      <WorkflowPanel />
      <BottomAISummaryPanel data={bottomAISummary} />
      </div>
    </TabLiveShell>
  );
}
