"use client";

import { TabLiveShell } from "@/components/platform/TabLiveShell";
import { Eye } from "lucide-react";
import { Button } from "@/components/ui/button";
import { HorizontalBarChart } from "@/components/scan-chain/charts/BarCharts";
import { DonutChart, DistributionPie } from "@/components/scan-chain/charts/PieCharts";
import { ChartCard } from "@/components/scan-chain/ChartCard";
import { DataTable, StatusBadge } from "@/components/scan-chain/DataTable";
import { MBISTAIDiagnosisCard } from "@/components/mbist/MBISTAIDiagnosisCard";
import { MBISTHeatmap } from "@/components/mbist/MBISTHeatmap";
import { KPIGrid } from "@/components/mbist/KPICard";
import { useFilteredMbistData } from "@/hooks/useMbistData";

export function OverviewTab() {
  const liveData = useFilteredMbistData();
  const {aiDiagnosisSummary,
    failureByBank,
    failureTypeDistribution,
    memoryHealthData,
    overviewKPIs,
    recentFailures,
  } = liveData;
  const bankData = failureByBank.map((b) => ({ chip: b.bank, failCount: b.failCount }));

  return (
    <TabLiveShell module="mbist" hookResult={liveData}>
      <div className="dashboard-content">
      <KPIGrid data={overviewKPIs} />
      <div className="grid gap-6 lg:grid-cols-3">
        <ChartCard title="Memory Health Distribution" subtitle="Passed, failed, repairable, unknown" className="lg:col-span-1">
          <DonutChart data={memoryHealthData} centerLabel="Total Memories" centerValue="1,306" />
          <div className="mt-4 flex flex-wrap gap-3">
            {memoryHealthData.map((seg) => (
              <div key={seg.name} className="flex items-center gap-1.5 text-xs text-slate-400">
                <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: seg.color }} />
                {seg.name}: {seg.value}
              </div>
            ))}
          </div>
        </ChartCard>
        <ChartCard title="Memory Failure by Bank" subtitle="Top 10 banks by failure count" className="lg:col-span-2">
          <HorizontalBarChart data={bankData} />
        </ChartCard>
      </div>
      <MBISTHeatmap />
      <DataTable
        title="Recent MBIST Failures"
        subtitle="Latest memory BIST failures requiring attention"
        data={recentFailures}
        rowKey="memoryId"
        searchKeys={["memoryId", "memoryType", "bank", "address", "failureType"]}
        searchPlaceholder="Search failures..."
        pageSize={5}
        columns={[
          { key: "memoryId", label: "Memory ID", render: (row) => <span className="font-mono text-xs font-medium text-white">{row.memoryId}</span> },
          { key: "memoryType", label: "Memory Type" },
          { key: "bank", label: "Bank" },
          { key: "address", label: "Address", render: (row) => <span className="font-mono text-xs">{row.address}</span> },
          { key: "failureType", label: "Failure Type" },
          { key: "status", label: "Status", render: (row) => <StatusBadge status={row.status} variant={row.status === "Critical" ? "danger" : row.status === "Warning" ? "warning" : "danger"} /> },
          { key: "repairStatus", label: "Repair Status", render: (row) => {
            const v = row.repairStatus === "Repaired" ? "success" : row.repairStatus === "In Progress" ? "info" : row.repairStatus === "Not Repairable" ? "danger" : "warning";
            return <StatusBadge status={row.repairStatus} variant={v} />;
          }},
          { key: "timestamp", label: "Timestamp" },
          { key: "action", label: "Action", sortable: false, render: () => <Button variant="ghost" size="sm" className="h-7 text-xs text-[#7C3AED]"><Eye className="mr-1 h-3 w-3" />View</Button> },
        ]}
      />
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Failure Type Distribution" subtitle="Breakdown by fault category">
          <DistributionPie data={failureTypeDistribution} />
        </ChartCard>
        <MBISTAIDiagnosisCard data={aiDiagnosisSummary} />
      </div>
      </div>
    </TabLiveShell>
  );
}
