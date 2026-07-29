"use client";

import { TabLiveShell } from "@/components/platform/TabLiveShell";
import { VerticalBarChart } from "@/components/scan-chain/charts/BarCharts";
import { TrendLineChart } from "@/components/scan-chain/charts/LineCharts";
import { DistributionPie } from "@/components/scan-chain/charts/PieCharts";
import { ChartCard } from "@/components/scan-chain/ChartCard";
import { DataTable } from "@/components/scan-chain/DataTable";
import { SeverityBadge } from "@/components/alerts/Badges";
import { KPIGrid } from "@/components/alerts/KPICard";
import { useFilteredAlertsData } from "@/hooks/useAlertsData";

export function MbistAlertsTab() {
  const liveData = useFilteredAlertsData();
  const {mbistAlerts, mbistKPIs, moduleAlertTrend } = liveData;

  return (
    <TabLiveShell module="alerts" hookResult={liveData}>
      <div className="dashboard-content">
      <KPIGrid data={mbistKPIs} />
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Memory Alert Trend" subtitle="Weekly MBIST alerts">
          <TrendLineChart data={moduleAlertTrend(14)} lines={[{ key: "value", color: "#06B6D4", name: "Alerts" }]} />
        </ChartCard>
        <ChartCard title="Failure by Bank" subtitle="Alerts per memory bank">
          <VerticalBarChart data={[{ label: "Bank-0", value: 6 }, { label: "Bank-1", value: 4 }, { label: "Bank-2", value: 8 }, { label: "Bank-4", value: 3 }]} color="#06B6D4" />
        </ChartCard>
        <ChartCard title="Repair Status" subtitle="Repair alert breakdown">
          <DistributionPie data={[{ name: "Pending", value: 38, color: "#F97316" }, { name: "In Progress", value: 32, color: "#06B6D4" }, { name: "Failed", value: 30, color: "#EF4444" }]} />
        </ChartCard>
      </div>
      <DataTable
        title="MBIST Alerts"
        subtitle="Memory failures, repair failures, and bank errors"
        data={mbistAlerts}
        rowKey="id"
        searchKeys={["id", "memory", "bank", "recommendation"]}
        searchPlaceholder="Search MBIST alerts..."
        columns={[
          { key: "id", label: "Alert ID", render: (row) => <span className="font-mono text-xs text-white">{row.id}</span> },
          { key: "memory", label: "Memory" },
          { key: "bank", label: "Bank" },
          { key: "severity", label: "Severity", render: (row) => <SeverityBadge severity={row.severity} /> },
          { key: "recommendation", label: "Recommendation" },
        ]}
      />
      </div>
    </TabLiveShell>
  );
}
