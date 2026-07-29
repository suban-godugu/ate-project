"use client";

import { useEffect } from "react";
import { AlertTriangle } from "lucide-react";
import { KpiDrillDownWorkspace } from "@/components/common/kpi-drilldown/KpiDrillDownWorkspace";
import { WorkspaceSkeleton } from "@/components/common/kpi-drilldown/KpiWorkspaceSections";
import { Button } from "@/components/ui/button";
import { useKpiDrillDownWorkspace } from "@/hooks/useKpiDrillDownWorkspace";
import { workspaceLayoutPreset } from "@/lib/kpiDrillDown/kpiDrillDownUtils";
import { cn } from "@/lib/utils";
import type { DrillDownKPI } from "@/types/kpiDrillDown";

interface KpiDrillDownModalProps {
  kpi: DrillDownKPI | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function KpiDrillDownModal({ kpi, open, onOpenChange }: KpiDrillDownModalProps) {
  const { workspace, filters, updateFilters, refresh, isLoading, error, isEmpty, isLive } = useKpiDrillDownWorkspace(open ? kpi : null);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onOpenChange(false);
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open, onOpenChange]);

  if (!open || !kpi) return null;

  const layoutPreset = workspaceLayoutPreset(kpi.id);
  const compactClass =
    layoutPreset === "failure" || layoutPreset === "diagnosis" || layoutPreset === "optimization" || layoutPreset === "debug"
      ? "h-[92vh] w-[95vw]"
      : "h-[90vh] w-[90vw]";

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <button
        type="button"
        aria-label="Close analytics workspace overlay"
        className="absolute inset-0 bg-black/80 backdrop-blur-md"
        onClick={() => onOpenChange(false)}
      />
      <div className="relative z-10">
        {isLoading && <WorkspaceSkeleton layoutPreset={layoutPreset} />}
        {!isLoading && error && (
          <div className={cn("flex max-w-[600px] flex-col items-center justify-center gap-4 rounded-2xl border border-red-500/30 bg-[#0B0F1A]/95 p-8 text-center", compactClass)}>
            <AlertTriangle className="h-10 w-10 text-red-400" />
            <p className="text-sm text-[#CBD5E1]">{error}</p>
            <div className="flex gap-2">
              <Button type="button" onClick={refresh}>
                Retry
              </Button>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Close
              </Button>
            </div>
          </div>
        )}
        {!isLoading && !error && isEmpty && (
          <div className={cn("flex max-w-[600px] flex-col items-center justify-center gap-4 rounded-2xl border border-[#2D3748] bg-[#0B0F1A]/95 p-8 text-center", compactClass)}>
            <p className="text-sm text-[#94A3B8]">No analytics data available for this KPI.</p>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Close
            </Button>
          </div>
        )}
        {!isLoading && !error && workspace && (
          <KpiDrillDownWorkspace
            workspace={workspace}
            filters={filters}
            onFiltersChange={updateFilters}
            onRefresh={refresh}
            onClose={() => onOpenChange(false)}
            dataSource={isLive ? "fastapi" : "mock"}
          />
        )}
      </div>
    </div>
  );
}
