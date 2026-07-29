"use client";

import { TabLiveShell } from "@/components/platform/TabLiveShell";
import { Eye } from "lucide-react";
import { Button } from "@/components/ui/button";
import { HorizontalBarChart } from "@/components/scan-chain/charts/BarCharts";
import { DonutChart, DistributionPie } from "@/components/scan-chain/charts/PieCharts";
import { ChartCard } from "@/components/scan-chain/ChartCard";
import { DataTable, StatusBadge } from "@/components/scan-chain/DataTable";
import { LBISTAIDiagnosisCard } from "@/components/lbist/LBISTAIDiagnosisCard";
import { LBISTHeatmap } from "@/components/lbist/LBISTHeatmap";
import { KPIGrid } from "@/components/lbist/KPICard";
import { useFilteredLbistData } from "@/hooks/useLbistData";

export function OverviewTab() {
  const liveData = useFilteredLbistData();
  const {aiDiagnosisSummary,
    coverageDistribution,
    failureByModule,
    failureTypeDistribution,
    overviewKPIs,
    recentFailures,
  } = liveData;
  const moduleData = failureByModule.map((m) => ({ chip: m.module, failCount: m.failCount }));

  return (
    <TabLiveShell module="lbist" hookResult={liveData}>
      <div className="dashboard-content">
      <KPIGrid data={overviewKPIs} />
      <div className="grid gap-6 lg:grid-cols-3">
        <ChartCard title="LBIST Coverage Distribution" subtitle="Passed, failed, partial, untested" className="lg:col-span-1">
          <DonutChart data={coverageDistribution} centerLabel="Total Logic Blocks" centerValue="3,842" />
          <div className="mt-4 flex flex-wrap gap-3">
            {coverageDistribution.map((seg) => (
              <div key={seg.name} className="flex items-center gap-1.5 text-xs text-slate-400">
                <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: seg.color }} />
                {seg.name}: {seg.value}
              </div>
            ))}
          </div>
        </ChartCard>
        <ChartCard title="Logic Failure by Module" subtitle="Top 10 logic modules by failure count" className="lg:col-span-2">
          <HorizontalBarChart data={moduleData} />
        </ChartCard>
      </div>
      <LBISTHeatmap />
      <DataTable
        title="Recent LBIST Failures"
        subtitle="Latest logic BIST session failures"
        data={recentFailures}
        rowKey="sessionId"
        searchKeys={["sessionId", "logicBlock", "controller", "misrSignature"]}
        searchPlaceholder="Search failures..."
        pageSize={5}
        columns={[
          { key: "sessionId", label: "Session ID", render: (row) => <span className="font-mono text-xs font-medium text-white">{row.sessionId}</span> },
          { key: "logicBlock", label: "Logic Block" },
          { key: "controller", label: "Controller" },
          { key: "misrSignature", label: "MISR Signature", render: (row) => <span className="font-mono text-xs">{row.misrSignature}</span> },
          { key: "expectedSignature", label: "Expected Signature", render: (row) => <span className="font-mono text-xs">{row.expectedSignature}</span> },
          { key: "coverage", label: "Coverage %", render: (row) => `${row.coverage}%` },
          { key: "status", label: "Status", render: (row) => <StatusBadge status={row.status} variant={row.status === "Critical" ? "danger" : row.status === "Warning" ? "warning" : "danger"} /> },
          { key: "timestamp", label: "Timestamp" },
          { key: "action", label: "Action", sortable: false, render: () => <Button variant="ghost" size="sm" className="h-7 text-xs text-[#7C3AED]"><Eye className="mr-1 h-3 w-3" />View</Button> },
        ]}
      />
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Failure Distribution" subtitle="Breakdown by fault type">
          <DistributionPie data={failureTypeDistribution} />
        </ChartCard>
        <LBISTAIDiagnosisCard data={aiDiagnosisSummary} />
      </div>
      </div>
    </TabLiveShell>
  );
}
