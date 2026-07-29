"use client";

import { Pencil, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DataTable } from "@/components/scan-chain/DataTable";
import { AlertStatusBadge, ModuleBadge, SeverityBadge } from "@/components/alerts/Badges";
import { isLiveApi } from "@/lib/api/config";
import type { RecentAlertRow } from "@/types/alerts";

interface AlertsOverviewTableProps {
  data: RecentAlertRow[];
  onEdit: (row: RecentAlertRow) => void;
  onDelete: (row: RecentAlertRow) => void;
}

export function AlertsOverviewTable({ data, onEdit, onDelete }: AlertsOverviewTableProps) {
  const live = isLiveApi();

  return (
    <DataTable
      title="Recent Alerts"
      subtitle="Real-time alerts consolidated from all analysis modules"
      data={data}
      rowKey="id"
      searchKeys={["id", "sourceModule", "lotId", "waferId", "description", "assignedEngineer"]}
      searchPlaceholder="Search alerts, lots, wafers..."
      pageSize={5}
      columns={[
        {
          key: "id",
          label: "Alert ID",
          render: (row) => <span className="font-mono text-xs text-white">{row.id}</span>,
        },
        {
          key: "sourceModule",
          label: "Source Module",
          render: (row) => <ModuleBadge module={row.sourceModule} />,
        },
        { key: "lotId", label: "Lot ID" },
        { key: "waferId", label: "Wafer ID" },
        {
          key: "severity",
          label: "Severity",
          render: (row) => <SeverityBadge severity={row.severity} />,
        },
        { key: "description", label: "Description" },
        {
          key: "status",
          label: "Status",
          render: (row) => <AlertStatusBadge status={row.status} />,
        },
        { key: "assignedEngineer", label: "Assigned Engineer" },
        { key: "createdTime", label: "Created Time" },
        {
          key: "action",
          label: "Actions",
          sortable: false,
          render: (row) =>
            live ? (
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 text-xs text-[#7C3AED]"
                  onClick={() => onEdit(row)}
                >
                  <Pencil className="mr-1 h-3 w-3" />
                  Edit
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 text-xs text-red-400"
                  onClick={() => onDelete(row)}
                >
                  <Trash2 className="mr-1 h-3 w-3" />
                  Delete
                </Button>
              </div>
            ) : (
              <span className="text-xs text-slate-500">—</span>
            ),
        },
      ]}
    />
  );
}
