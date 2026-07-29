"use client";

import { TabLiveShell } from "@/components/platform/TabLiveShell";
import { VerticalBarChart } from "@/components/scan-chain/charts/BarCharts";
import { TrendLineChart } from "@/components/scan-chain/charts/LineCharts";
import { DistributionPie } from "@/components/scan-chain/charts/PieCharts";
import { ChartCard } from "@/components/scan-chain/ChartCard";
import { DataTable, StatusBadge } from "@/components/scan-chain/DataTable";
import { KPIGrid } from "@/components/mbist/KPICard";
import { MBISTHeatmap } from "@/components/mbist/MBISTHeatmap";
import { useFilteredMbistData } from "@/hooks/useMbistData";

export function FailureAnalysisTab() {
  const liveData = useFilteredMbistData();
  const {failureByBankChart,
    failureByType,
    failureKPIs,
    failureRecords,
    failureTrend,
    failureTypeDistribution,
  } = liveData;

  return (
    <TabLiveShell module="mbist" hookResult={liveData}>
      <div className="dashboard-content">
      <KPIGrid data={failureKPIs} />
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Failure Trend" subtitle="Total vs. critical failures">
          <TrendLineChart data={failureTrend} lines={[{ key: "value", color: "#EF4444", name: "Total" }, { key: "value2", color: "#F97316", name: "Critical" }]} />
        </ChartCard>
        <ChartCard title="Failure Type Distribution" subtitle="Fault category breakdown">
          <DistributionPie data={failureTypeDistribution} />
        </ChartCard>
        <ChartCard title="Failure by Memory Type" subtitle="Failures grouped by memory type">
          <VerticalBarChart data={failureByType} color="#EF4444" />
        </ChartCard>
        <ChartCard title="Failure by Bank" subtitle="Bank-level failure distribution">
          <VerticalBarChart data={failureByBankChart} color="#F97316" />
        </ChartCard>
      </div>
      <MBISTHeatmap />
      <DataTable
        title="Failure Records"
        subtitle="Complete MBIST failure log"
        data={failureRecords}
        rowKey="failureId"
        searchKeys={["failureId", "memoryId", "bank", "failType"]}
        searchPlaceholder="Search records..."
        columns={[
          { key: "failureId", label: "Failure ID", render: (row) => <span className="font-mono text-xs text-white">{row.failureId}</span> },
          { key: "memoryId", label: "Memory ID" },
          { key: "memoryType", label: "Memory Type" },
          { key: "bank", label: "Bank" },
          { key: "failType", label: "Fail Type" },
          { key: "severity", label: "Severity", render: (row) => <StatusBadge status={row.severity} variant={row.severity === "Critical" ? "danger" : row.severity === "Warning" ? "warning" : "success"} /> },
          { key: "timestamp", label: "Timestamp" },
        ]}
      />
      </div>
    </TabLiveShell>
  );
}
