"use client";

import { ArrowLeft } from "lucide-react";

import { useAnalysis } from "@/hooks/useAnalysis";
import { isLotDashboardTab, type DashboardTab } from "@/types/wafer";
import { defectFromLotCode } from "@/utils/lotTaxonomy";

function formatParentLabel(tab: DashboardTab | null): string {
  if (!tab || tab === "spatial" || tab === "zones") {
    return "Wafer Analysis";
  }
  if (isLotDashboardTab(tab)) {
    const defect = defectFromLotCode(tab);
    return defect ? `${tab} (${defect})` : tab;
  }
  if (tab === "wafer") return "Wafer Analysis";
  return "Wafer Analysis";
}

/**
 * Child-page chrome for Spatial Analytics / Engineering Zones.
 * Returns to Wafer Analysis (modal view or parent tab) without resetting session state.
 */
export function AnalysisChildNav({
  child,
}: {
  child: "spatial" | "zones";
}) {
  const {
    activeTab,
    analysisReturnTab,
    isWaferModalOpen,
    returnToWaferAnalysis,
  } = useAnalysis();

  const parentTab = isWaferModalOpen
    ? activeTab
    : (analysisReturnTab ?? activeTab);
  const parentLabel = formatParentLabel(parentTab);
  const childLabel =
    child === "spatial" ? "Spatial Analytics" : "Engineering Zone Analysis";

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={returnToWaferAnalysis}
        className="inline-flex items-center gap-1.5 text-sm font-medium text-signal-info transition hover:underline"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Wafer Analysis
      </button>
      <nav
        aria-label="Analysis breadcrumb"
        className="flex flex-wrap items-center gap-1.5 text-xs text-[var(--muted)]"
      >
        <button
          type="button"
          onClick={returnToWaferAnalysis}
          className="font-medium text-[var(--foreground)] hover:underline"
        >
          {parentLabel}
        </button>
        <span aria-hidden="true">›</span>
        <span>Wafer Analysis</span>
        <span aria-hidden="true">›</span>
        <span className="font-medium text-[var(--foreground)]">{childLabel}</span>
      </nav>
    </div>
  );
}
