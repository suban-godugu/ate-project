"use client";

import type { DashboardTab } from "@/wafervision/types";
import { useAnalysis } from "@/wafervision/hooks/useAnalysis";
import { LOT_TAXONOMY, lotLabel } from "@/wafervision/utils/lotTaxonomy";
import { cn } from "@/wafervision/utils/format";

const MAIN_TABS: { id: DashboardTab; label: string }[] = [
  { id: "overview", label: "Overview" },
  ...LOT_TAXONOMY.map(({ lot }) => ({ id: lot as DashboardTab, label: lotLabel(lot) })),
  { id: "reports", label: "Reports" },
];

export function DashboardTabs() {
  const { activeTab, setActiveTab, analysisReturnTab } = useAnalysis();

  const highlightParent =
    analysisReturnTab &&
    (activeTab === "spatial" || activeTab === "zones") &&
    analysisReturnTab;

  return (
    <nav
      className="flex flex-wrap gap-1 border-b border-[#2D3748] pb-px"
      aria-label="Wafer analysis tabs"
      role="tablist"
    >
      {MAIN_TABS.map(({ id, label }) => {
        const isActive = activeTab === id || highlightParent === id;
        return (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={isActive}
            onClick={() => setActiveTab(id)}
            className={cn(
              "rounded-t-lg px-3 py-2 text-sm font-medium transition",
              isActive
                ? "bg-[#7C3AED] text-white shadow-[0_0_20px_rgba(124,58,237,0.35)]"
                : "text-slate-400 hover:bg-[#7C3AED]/10 hover:text-white"
            )}
          >
            {label}
          </button>
        );
      })}
    </nav>
  );
}
