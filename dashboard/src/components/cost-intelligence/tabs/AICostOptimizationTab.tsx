"use client";

import { TabLiveShell } from "@/components/platform/TabLiveShell";
import { Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DataTable } from "@/components/scan-chain/DataTable";
import { CostOptimizationEnginePanel, EnterpriseCostSummaryPanel, ModuleBadge, PriorityBadge } from "@/components/cost-intelligence/CostPanels";
import { useFilteredCostIntelligenceData } from "@/hooks/useCostIntelligenceData";

export function AICostOptimizationTab() {
  const liveData = useFilteredCostIntelligenceData();
  const {aiCostRecommendations, enterpriseCostSummary } = liveData;

  return (
    <TabLiveShell module="cost-intelligence" hookResult={liveData}>
      <div className="dashboard-content">
      <CostOptimizationEnginePanel />
      <DataTable
        title="AI Cost Recommendations"
        subtitle="Cross-module optimization with projected savings"
        data={aiCostRecommendations}
        rowKey="issue"
        searchKeys={["module", "issue", "recommendation"]}
        searchPlaceholder="Search modules, issues, recommendations..."
        pageSize={6}
        columns={[
          { key: "module", label: "Module", render: (row) => <ModuleBadge module={row.module} /> },
          { key: "issue", label: "Issue" },
          { key: "currentCost", label: "Current Cost" },
          { key: "optimizedCost", label: "Optimized Cost", render: (row) => <span className="text-emerald-400">{row.optimizedCost}</span> },
          { key: "savings", label: "Savings", render: (row) => <span className="font-medium text-emerald-400">{row.savings}</span> },
          { key: "priority", label: "Priority", render: (row) => <PriorityBadge priority={row.priority} /> },
          { key: "confidence", label: "Confidence", render: (row) => `${row.confidence}%` },
          { key: "recommendation", label: "Recommendation" },
        ]}
      />
      <EnterpriseCostSummaryPanel data={enterpriseCostSummary} />
      <div className="flex justify-end">
        <Button size="sm" className="btn-glow rounded-xl bg-[#7C3AED] text-xs hover:bg-[#6D28D9]">
          <Sparkles className="mr-1.5 h-3.5 w-3.5" />
          Generate Final Cost Report
        </Button>
      </div>
      </div>
    </TabLiveShell>
  );
}
