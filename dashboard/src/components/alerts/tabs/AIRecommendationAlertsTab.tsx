"use client";

import { TabLiveShell } from "@/components/platform/TabLiveShell";
import { VerticalBarChart } from "@/components/scan-chain/charts/BarCharts";
import { TrendLineChart } from "@/components/scan-chain/charts/LineCharts";
import { DistributionPie } from "@/components/scan-chain/charts/PieCharts";
import { ChartCard } from "@/components/scan-chain/ChartCard";
import { DataTable } from "@/components/scan-chain/DataTable";
import { AlertStatusBadge, ModuleBadge, SeverityBadge } from "@/components/alerts/Badges";
import { KPIGrid } from "@/components/alerts/KPICard";
import { useFilteredAlertsData } from "@/hooks/useAlertsData";

export function AIRecommendationAlertsTab() {
  const liveData = useFilteredAlertsData();
  const {aiRecommendationAlerts, aiRecKPIs, moduleAlertTrend } = liveData;

  return (
    <TabLiveShell module="alerts" hookResult={liveData}>
      <div className="dashboard-content">
      <KPIGrid data={aiRecKPIs} />
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Recommendation Trend" subtitle="Weekly AI recommendation alerts">
          <TrendLineChart data={moduleAlertTrend(10)} lines={[{ key: "value", color: "#EC4899", name: "Alerts" }]} />
        </ChartCard>
        <ChartCard title="Priority Distribution" subtitle="By priority level">
          <VerticalBarChart data={[{ label: "Critical", value: 14 }, { label: "High", value: 18 }, { label: "Medium", value: 22 }, { label: "Low", value: 12 }]} color="#EC4899" />
        </ChartCard>
        <ChartCard title="Implementation Status" subtitle="Recommendation status breakdown">
          <DistributionPie data={[{ name: "Pending", value: 32, color: "#F97316" }, { name: "Open", value: 28, color: "#EF4444" }, { name: "Resolved", value: 40, color: "#22C55E" }]} />
        </ChartCard>
      </div>
      <DataTable
        title="AI Recommendation Alerts"
        subtitle="Pending actions, critical optimizations, and high ROI recommendations"
        data={aiRecommendationAlerts}
        rowKey="id"
        searchKeys={["id", "sourceModule", "engineer"]}
        searchPlaceholder="Search recommendation alerts..."
        columns={[
          { key: "id", label: "Recommendation ID", render: (row) => <span className="font-mono text-xs text-white">{row.id}</span> },
          { key: "sourceModule", label: "Source Module", render: (row) => <ModuleBadge module={row.sourceModule} /> },
          { key: "priority", label: "Priority", render: (row) => <SeverityBadge severity={row.priority} /> },
          { key: "confidence", label: "Confidence", render: (row) => `${row.confidence}%` },
          { key: "status", label: "Status", render: (row) => <AlertStatusBadge status={row.status} /> },
          { key: "engineer", label: "Engineer" },
        ]}
      />
      </div>
    </TabLiveShell>
  );
}
