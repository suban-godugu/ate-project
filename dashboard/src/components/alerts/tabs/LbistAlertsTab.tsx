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

export function LbistAlertsTab() {
  const liveData = useFilteredAlertsData();
  const {lbistAlerts, lbistKPIs, moduleAlertTrend } = liveData;

  return (
    <TabLiveShell module="alerts" hookResult={liveData}>
      <div className="dashboard-content">
      <KPIGrid data={lbistKPIs} />
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Logic Alert Trend" subtitle="Weekly LBIST alerts">
          <TrendLineChart data={moduleAlertTrend(12)} lines={[{ key: "value", color: "#F97316", name: "Alerts" }]} />
        </ChartCard>
        <ChartCard title="Coverage Issues" subtitle="Coverage-related alerts">
          <VerticalBarChart data={[{ label: "GPU", value: 4 }, { label: "NOC", value: 3 }, { label: "CPU", value: 5 }, { label: "DSP", value: 2 }]} color="#F97316" />
        </ChartCard>
        <ChartCard title="Failure Distribution" subtitle="Logic failure types">
          <DistributionPie data={[{ name: "Signature", value: 35, color: "#7C3AED" }, { name: "Coverage", value: 40, color: "#F97316" }, { name: "Runtime", value: 25, color: "#EF4444" }]} />
        </ChartCard>
      </div>
      <DataTable
        title="LBIST Alerts"
        subtitle="Logic failures, coverage issues, and signature mismatch"
        data={lbistAlerts}
        rowKey="id"
        searchKeys={["id", "logicBlock", "recommendation"]}
        searchPlaceholder="Search LBIST alerts..."
        columns={[
          { key: "id", label: "Alert ID", render: (row) => <span className="font-mono text-xs text-white">{row.id}</span> },
          { key: "logicBlock", label: "Logic Block" },
          { key: "severity", label: "Severity", render: (row) => <SeverityBadge severity={row.severity} /> },
          { key: "recommendation", label: "Recommendation" },
        ]}
      />
      </div>
    </TabLiveShell>
  );
}
