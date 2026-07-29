"use client";

import { TabLiveShell } from "@/components/platform/TabLiveShell";
import { VerticalBarChart } from "@/components/scan-chain/charts/BarCharts";
import { TrendLineChart } from "@/components/scan-chain/charts/LineCharts";
import { ChartCard } from "@/components/scan-chain/ChartCard";
import { DataTable } from "@/components/scan-chain/DataTable";
import { ModuleBadge } from "@/components/alerts/Badges";
import { KPIGrid } from "@/components/alerts/KPICard";
import { useFilteredAlertsData } from "@/hooks/useAlertsData";

export function CostAlertsTab() {
  const liveData = useFilteredAlertsData();
  const {costAlerts, costKPIs, moduleAlertTrend } = liveData;

  return (
    <TabLiveShell module="alerts" hookResult={liveData}>
      <div className="dashboard-content">
      <KPIGrid data={costKPIs} />
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Cost Trend" subtitle="Cost alert trend">
          <TrendLineChart data={moduleAlertTrend(6)} lines={[{ key: "value", color: "#EAB308", name: "Cost Alerts" }]} />
        </ChartCard>
        <ChartCard title="Cost by Module" subtitle="Alerts by test module">
          <VerticalBarChart data={[{ label: "Scan Chain", value: 5 }, { label: "MBIST", value: 3 }, { label: "LBIST", value: 2 }, { label: "Wafer", value: 4 }]} color="#EAB308" />
        </ChartCard>
        <ChartCard title="Budget Consumption" subtitle="Budget threshold alerts (%)">
          <VerticalBarChart data={[{ label: "Scan", value: 92 }, { label: "MBIST", value: 88 }, { label: "LBIST", value: 78 }, { label: "Wafer", value: 95 }]} color="#EF4444" />
        </ChartCard>
      </div>
      <DataTable
        title="Cost Alerts"
        subtitle="Budget exceeded, high test cost, and retest cost alerts"
        data={costAlerts}
        rowKey="id"
        searchKeys={["id", "module", "recommendation"]}
        searchPlaceholder="Search cost alerts..."
        columns={[
          { key: "id", label: "Alert ID", render: (row) => <span className="font-mono text-xs text-white">{row.id}</span> },
          { key: "module", label: "Module", render: (row) => <ModuleBadge module={row.module} /> },
          { key: "currentCost", label: "Current Cost" },
          { key: "threshold", label: "Threshold" },
          { key: "recommendation", label: "Recommendation" },
        ]}
      />
      </div>
    </TabLiveShell>
  );
}
