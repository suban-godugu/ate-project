"use client";

import { TabLiveShell } from "@/components/platform/TabLiveShell";
import { VerticalBarChart } from "@/components/scan-chain/charts/BarCharts";
import { TrendLineChart } from "@/components/scan-chain/charts/LineCharts";
import { DistributionPie } from "@/components/scan-chain/charts/PieCharts";
import { ChartCard } from "@/components/scan-chain/ChartCard";
import { DataTable } from "@/components/scan-chain/DataTable";
import { SeverityBadge } from "@/components/alerts/Badges";
import { KPIGrid } from "@/components/alerts/KPICard";
import { WaferAlertHeatmap } from "@/components/alerts/WaferAlertHeatmap";
import { useFilteredAlertsData } from "@/hooks/useAlertsData";

export function WaferAlertsTab() {
  const liveData = useFilteredAlertsData();
  const {moduleAlertTrend, waferAlerts, waferKPIs } = liveData;

  return (
    <TabLiveShell module="alerts" hookResult={liveData}>
      <div className="dashboard-content">
      <KPIGrid data={waferKPIs} />
      <WaferAlertHeatmap />
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Yield Trend" subtitle="Yield drop alerts over time">
          <TrendLineChart data={moduleAlertTrend(8)} lines={[{ key: "value", color: "#22C55E", name: "Yield Alerts" }]} />
        </ChartCard>
        <ChartCard title="Defect Distribution" subtitle="Defect density alert types">
          <DistributionPie data={[{ name: "Hotspot", value: 38, color: "#EF4444" }, { name: "Edge", value: 32, color: "#F97316" }, { name: "Center", value: 30, color: "#EAB308" }]} />
        </ChartCard>
      </div>
      <DataTable
        title="Wafer Alerts"
        subtitle="Yield drops, hotspots, and defect density alerts"
        data={waferAlerts}
        rowKey="id"
        searchKeys={["id", "lot", "wafer", "recommendation"]}
        searchPlaceholder="Search wafer alerts..."
        columns={[
          { key: "id", label: "Alert ID", render: (row) => <span className="font-mono text-xs text-white">{row.id}</span> },
          { key: "lot", label: "Lot" },
          { key: "wafer", label: "Wafer" },
          { key: "severity", label: "Severity", render: (row) => <SeverityBadge severity={row.severity} /> },
          { key: "recommendation", label: "Recommendation" },
        ]}
      />
      </div>
    </TabLiveShell>
  );
}
