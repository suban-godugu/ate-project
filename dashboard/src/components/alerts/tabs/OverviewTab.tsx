"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AlertFormDialog } from "@/components/alerts/AlertFormDialog";
import { DeleteAlertDialog } from "@/components/alerts/DeleteAlertDialog";
import { AlertsOverviewTable } from "@/components/alerts/AlertsOverviewTable";
import { TabLiveShell } from "@/components/platform/TabLiveShell";
import { VerticalBarChart } from "@/components/scan-chain/charts/BarCharts";
import { TrendLineChart } from "@/components/scan-chain/charts/LineCharts";
import { DonutChart } from "@/components/scan-chain/charts/PieCharts";
import { ChartCard } from "@/components/scan-chain/ChartCard";
import { AlertWorkflowPanel, CriticalAlertSummaryCard, ExecutiveAlertSummaryPanel } from "@/components/alerts/AlertPanels";
import { KPIGrid } from "@/components/alerts/KPICard";
import { useFilteredAlertsData } from "@/hooks/useAlertsData";
import type { RecentAlertRow } from "@/types/alerts";

export function OverviewTab() {
  const liveData = useFilteredAlertsData();
  const {
    alertDistribution,
    alertTrend,
    criticalAlertSummary,
    executiveAlertSummary,
    overviewKPIs,
    recentAlerts,
    severityDistribution,
  } = liveData;

  const [createOpen, setCreateOpen] = useState(false);
  const [editAlert, setEditAlert] = useState<RecentAlertRow | null>(null);
  const [deleteAlert, setDeleteAlert] = useState<RecentAlertRow | null>(null);

  return (
    <TabLiveShell module="alerts" hookResult={liveData}>
      <div className="dashboard-content">
        <div className="mb-4 flex justify-end">
          <Button
            onClick={() => setCreateOpen(true)}
            className="rounded-xl bg-[#7C3AED] hover:bg-[#6D28D9]"
          >
            <Plus className="mr-2 h-4 w-4" />
            New Alert
          </Button>
        </div>

        <KPIGrid data={overviewKPIs} />
        <div className="grid gap-6 lg:grid-cols-3">
          <ChartCard title="Alert Distribution" subtitle="By source module" className="lg:col-span-1">
            <DonutChart data={alertDistribution} centerLabel="Total" centerValue="248" />
            <div className="mt-4 flex flex-wrap gap-3">
              {alertDistribution.map((s) => (
                <div key={s.name} className="flex items-center gap-1.5 text-xs text-slate-400">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: s.color }} />
                  {s.name}: {s.value}%
                </div>
              ))}
            </div>
          </ChartCard>
          <ChartCard title="Alert Severity" subtitle="By severity level" className="lg:col-span-1">
            <VerticalBarChart data={severityDistribution} color="#EF4444" />
          </ChartCard>
          <ChartCard title="Alert Trend" subtitle="Last 30 days" className="lg:col-span-1">
            <TrendLineChart data={alertTrend} lines={[{ key: "value", color: "#7C3AED", name: "Alerts" }]} />
          </ChartCard>
        </div>

        <AlertsOverviewTable
          data={recentAlerts}
          onEdit={(row) => setEditAlert(row)}
          onDelete={(row) => setDeleteAlert(row)}
        />

        <CriticalAlertSummaryCard data={criticalAlertSummary} />
        <AlertWorkflowPanel />
        <ExecutiveAlertSummaryPanel data={executiveAlertSummary} />
      </div>

      <AlertFormDialog open={createOpen} onOpenChange={setCreateOpen} mode="create" />
      <AlertFormDialog
        open={!!editAlert}
        onOpenChange={(v) => !v && setEditAlert(null)}
        mode="edit"
        alert={editAlert}
      />
      <DeleteAlertDialog
        open={!!deleteAlert}
        onOpenChange={(v) => !v && setDeleteAlert(null)}
        alert={deleteAlert}
      />
    </TabLiveShell>
  );
}
