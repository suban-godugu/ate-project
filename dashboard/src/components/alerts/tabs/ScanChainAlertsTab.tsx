"use client";

import { TabLiveShell } from "@/components/platform/TabLiveShell";
import { VerticalBarChart } from "@/components/scan-chain/charts/BarCharts";
import { TrendLineChart } from "@/components/scan-chain/charts/LineCharts";
import { DistributionPie } from "@/components/scan-chain/charts/PieCharts";
import { ChartCard } from "@/components/scan-chain/ChartCard";
import { DataTable } from "@/components/scan-chain/DataTable";
import { AlertStatusBadge, SeverityBadge } from "@/components/alerts/Badges";
import { KPIGrid } from "@/components/alerts/KPICard";
import { useFilteredAlertsData } from "@/hooks/useAlertsData";

export function ScanChainAlertsTab() {
  const liveData = useFilteredAlertsData();
  const {moduleAlertTrend, scanChainAlerts, scanChainKPIs } = liveData;

  return (
    <TabLiveShell module="alerts" hookResult={liveData}>
      <div className="dashboard-content">
      <KPIGrid data={scanChainKPIs} />
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Alert Trend" subtitle="Weekly scan chain alerts">
          <TrendLineChart data={moduleAlertTrend(18)} lines={[{ key: "value", color: "#7C3AED", name: "Alerts" }]} />
        </ChartCard>
        <ChartCard title="Failure Distribution" subtitle="By failure type">
          <DistributionPie data={[{ name: "Pattern", value: 42, color: "#7C3AED" }, { name: "Coverage", value: 28, color: "#F97316" }, { name: "Diagnosis", value: 18, color: "#EF4444" }, { name: "Chain", value: 12, color: "#64748B" }]} />
        </ChartCard>
        <ChartCard title="Top Affected Chains" subtitle="Alert count by chain">
          <VerticalBarChart data={[{ label: "SC-4821", value: 8 }, { label: "SC-3156", value: 6 }, { label: "SC-7892", value: 5 }, { label: "SC-2441", value: 4 }]} color="#7C3AED" />
        </ChartCard>
      </div>
      <DataTable
        title="Scan Chain Alerts"
        subtitle="Pattern failures, coverage drops, and diagnosis errors"
        data={scanChainAlerts}
        rowKey="id"
        searchKeys={["id", "chainId", "pattern", "recommendation"]}
        searchPlaceholder="Search chain alerts..."
        columns={[
          { key: "id", label: "Alert ID", render: (row) => <span className="font-mono text-xs text-white">{row.id}</span> },
          { key: "chainId", label: "Chain ID" },
          { key: "pattern", label: "Pattern" },
          { key: "severity", label: "Severity", render: (row) => <SeverityBadge severity={row.severity} /> },
          { key: "recommendation", label: "Recommendation" },
          { key: "status", label: "Status", render: (row) => <AlertStatusBadge status={row.status} /> },
        ]}
      />
      </div>
    </TabLiveShell>
  );
}
