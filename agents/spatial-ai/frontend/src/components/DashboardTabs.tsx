"use client";

import { useAnalysis } from "@/hooks/useAnalysis";
import type { DashboardTab } from "@/types/wafer";
import { cn } from "@/utils/format";
import { LOT_TAXONOMY } from "@/utils/lotTaxonomy";

/**
 * Global top navigation.
 * Spatial Analytics / Engineering Zones remain available from LOT wafer analysis
 * cards — not listed here.
 */
const TABS: { id: DashboardTab; label: string }[] = [
  { id: "overview", label: "Overview" },
  ...LOT_TAXONOMY.map(({ lot, defect }) => ({
    id: lot as DashboardTab,
    label: `${lot} (${defect})`,
  })),
  { id: "reports", label: "Reports" },
];

export function DashboardTabs() {
  const { activeTab, analysisReturnTab, setActiveTab } = useAnalysis();

  // While on Spatial / Zones child views, keep the parent LOT (or Wafer) tab highlighted.
  const highlightedTab =
    activeTab === "spatial" || activeTab === "zones"
      ? (analysisReturnTab ?? activeTab)
      : activeTab;

  return (
    <nav className="mb-4 flex flex-wrap gap-1 border-b border-[var(--line)] pb-2">
      {TABS.map((tab) => {
        const active = highlightedTab === tab.id;
        return (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "rounded-lg px-3 py-2 text-sm font-medium transition",
              active
                ? "bg-ink-800 text-white dark:bg-ink-200 dark:text-ink-950"
                : "text-[var(--muted)] hover:bg-ink-100 dark:hover:bg-ink-800",
            )}
          >
            {tab.label}
          </button>
        );
      })}
    </nav>
  );
}
