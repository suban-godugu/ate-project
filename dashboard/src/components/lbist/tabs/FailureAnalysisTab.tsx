"use client";

import { TabLiveShell } from "@/components/platform/TabLiveShell";
import { VerticalBarChart } from "@/components/scan-chain/charts/BarCharts";
import { TrendLineChart } from "@/components/scan-chain/charts/LineCharts";
import { DistributionPie } from "@/components/scan-chain/charts/PieCharts";
import { ChartCard } from "@/components/scan-chain/ChartCard";
import { DataTable, StatusBadge } from "@/components/scan-chain/DataTable";
import { KPIGrid } from "@/components/lbist/KPICard";
import { LBISTHeatmap } from "@/components/lbist/LBISTHeatmap";
import { useFilteredLbistData } from "@/hooks/useLbistData";

export function FailureAnalysisTab() {
  const liveData = useFilteredLbistData();
  const {failureByBlock,
    failureDensity,
    failureKPIs,
    failureRecords,
    failureTrend,
    failureTypeDistribution,
    logicFailureSummary,
  } = liveData;

  return (
    <TabLiveShell module="lbist" hookResult={liveData}>
      <div className="dashboard-content">
      <KPIGrid data={failureKPIs} />
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Failure Trend" subtitle="Total vs. critical failures">
          <TrendLineChart data={failureTrend} lines={[{ key: "value", color: "#EF4444", name: "Total" }, { key: "value2", color: "#F97316", name: "Critical" }]} />
        </ChartCard>
        <ChartCard title="Fault Distribution" subtitle="Failure type breakdown">
          <DistributionPie data={failureTypeDistribution} />
        </ChartCard>
        <ChartCard title="Failure by Logic Block" subtitle="Failures grouped by logic block">
          <VerticalBarChart data={failureByBlock} color="#EF4444" />
        </ChartCard>
        <ChartCard title="Failure Density" subtitle="Spatial failure density zones">
          <VerticalBarChart data={failureDensity} color="#F97316" />
        </ChartCard>
      </div>
      <LBISTHeatmap />
      <div className="grid gap-6 lg:grid-cols-2">
        <DataTable
          title="Failure Records"
          subtitle="Complete LBIST failure log"
          data={failureRecords}
          rowKey="failureId"
          searchKeys={["failureId", "sessionId", "logicBlock", "failType"]}
          searchPlaceholder="Search records..."
          columns={[
            { key: "failureId", label: "Failure ID", render: (row) => <span className="font-mono text-xs text-white">{row.failureId}</span> },
            { key: "sessionId", label: "Session ID" },
            { key: "logicBlock", label: "Logic Block" },
            { key: "failType", label: "Fail Type" },
            { key: "severity", label: "Severity", render: (row) => <StatusBadge status={row.severity} variant={row.severity === "Critical" ? "danger" : row.severity === "Warning" ? "warning" : "success"} /> },
            { key: "timestamp", label: "Timestamp" },
          ]}
        />
        <DataTable
          title="Logic Failure Summary"
          subtitle="Aggregated failure summary by logic block"
          data={logicFailureSummary}
          rowKey="logicBlock"
          searchKeys={["logicBlock", "module"]}
          searchPlaceholder="Search blocks..."
          pageSize={4}
          columns={[
            { key: "logicBlock", label: "Logic Block" },
            { key: "module", label: "Module" },
            { key: "failCount", label: "Fail Count" },
            { key: "coverage", label: "Coverage", render: (row) => `${row.coverage}%` },
            { key: "status", label: "Status", render: (row) => <StatusBadge status={row.status} variant={row.status === "Resolved" ? "success" : row.status === "Escalated" ? "danger" : "warning"} /> },
          ]}
        />
      </div>
      </div>
    </TabLiveShell>
  );
}
