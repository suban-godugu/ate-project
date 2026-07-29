"use client";

import { useEffect, useMemo, useRef } from "react";
import { ArrowLeft, ChevronLeft, ChevronRight, X } from "lucide-react";

import { AnalysisChildNav } from "@/components/AnalysisChildNav";
import {
  EngineeringZonesPanel,
  SpatialAnalyticsPanel,
} from "@/components/SpatialAnalyticsPanel";
import { WaferAnalysisContent } from "@/components/WaferAnalysisContent";
import { useAnalysis } from "@/hooks/useAnalysis";
import { isLotDashboardTab } from "@/types/wafer";
import { wafersInLot } from "@/utils/batchAggregates";
import { defectFromLotCode } from "@/utils/lotTaxonomy";
import { readWaferName } from "@/utils/format";

/**
 * Full-screen drawer for LOT wafer analysis.
 * Reuses existing analysis panels; Spatial / Zones are child views inside the same shell.
 */
export function WaferAnalysisModal() {
  const {
    results,
    selectedIndex,
    selected,
    activeTab,
    isWaferModalOpen,
    waferModalView,
    closeWaferAnalysisModal,
    selectWafer,
  } = useAnalysis();

  const bodyRef = useRef<HTMLDivElement>(null);

  const lotMembers = useMemo(() => {
    if (!isLotDashboardTab(activeTab)) return [];
    return wafersInLot(results, activeTab);
  }, [results, activeTab]);

  const positionInLot = useMemo(() => {
    return lotMembers.findIndex((m) => m.index === selectedIndex);
  }, [lotMembers, selectedIndex]);

  const lotLabel = useMemo(() => {
    if (!isLotDashboardTab(activeTab)) return "LOT";
    const defect = defectFromLotCode(activeTab);
    return defect ? `${activeTab} (${defect})` : activeTab;
  }, [activeTab]);

  useEffect(() => {
    if (!isWaferModalOpen) return;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        closeWaferAnalysisModal();
      }
    };
    window.addEventListener("keydown", onKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [isWaferModalOpen, closeWaferAnalysisModal]);

  useEffect(() => {
    if (!isWaferModalOpen) return;
    bodyRef.current?.scrollTo(0, 0);
  }, [isWaferModalOpen, selectedIndex, waferModalView]);

  if (!isWaferModalOpen) return null;

  const goPrev = () => {
    if (lotMembers.length === 0) return;
    const nextPos =
      positionInLot <= 0 ? lotMembers.length - 1 : positionInLot - 1;
    selectWafer(lotMembers[nextPos].index);
  };

  const goNext = () => {
    if (lotMembers.length === 0) return;
    const nextPos =
      positionInLot < 0 || positionInLot >= lotMembers.length - 1
        ? 0
        : positionInLot + 1;
    selectWafer(lotMembers[nextPos].index);
  };

  const waferOrdinal = positionInLot >= 0 ? positionInLot + 1 : "—";
  const waferTotal = lotMembers.length;

  return (
    <div
      className="fixed inset-0 z-[60] flex items-stretch justify-end"
      role="dialog"
      aria-modal="true"
      aria-label="Wafer Analysis"
    >
      <button
        type="button"
        className="absolute inset-0 bg-ink-950/50 backdrop-blur-[2px]"
        aria-label="Close wafer analysis"
        onClick={closeWaferAnalysisModal}
      />

      <div className="relative z-[61] flex h-full w-full max-w-[1400px] flex-col bg-[var(--background)] shadow-2xl">
        <header className="sticky top-0 z-10 flex flex-wrap items-center justify-between gap-3 border-b border-[var(--line)] bg-[var(--background)] px-4 py-3 md:px-6">
          <div className="flex min-w-0 flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={closeWaferAnalysisModal}
              className="inline-flex items-center gap-1.5 text-sm font-medium text-signal-info transition hover:underline"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to LOT
            </button>
            <span className="hidden text-[var(--muted)] sm:inline" aria-hidden="true">
              |
            </span>
            <p className="truncate text-sm text-[var(--muted)]">
              {lotLabel}
              {selected ? (
                <>
                  {" "}
                  ·{" "}
                  <span className="font-mono text-[var(--foreground)]">
                    {readWaferName(selected)}
                  </span>
                </>
              ) : null}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {waferTotal > 0 ? (
              <>
                <button
                  type="button"
                  onClick={goPrev}
                  className="inline-flex items-center gap-1 rounded-lg border border-[var(--line)] px-2.5 py-1.5 text-sm transition hover:bg-ink-100 dark:hover:bg-ink-800"
                >
                  <ChevronLeft className="h-4 w-4" />
                  Previous Wafer
                </button>
                <span className="min-w-[5.5rem] text-center font-mono text-sm tabular-nums">
                  Wafer {waferOrdinal} / {waferTotal}
                </span>
                <button
                  type="button"
                  onClick={goNext}
                  className="inline-flex items-center gap-1 rounded-lg border border-[var(--line)] px-2.5 py-1.5 text-sm transition hover:bg-ink-100 dark:hover:bg-ink-800"
                >
                  Next Wafer
                  <ChevronRight className="h-4 w-4" />
                </button>
              </>
            ) : null}
            <button
              type="button"
              onClick={closeWaferAnalysisModal}
              className="rounded-lg p-2 text-[var(--muted)] transition hover:bg-ink-100 hover:text-[var(--foreground)] dark:hover:bg-ink-800"
              aria-label="Close"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </header>

        <div ref={bodyRef} className="flex-1 overflow-y-auto px-4 py-5 md:px-6">
          {waferModalView === "analysis" ? <WaferAnalysisContent /> : null}
          {waferModalView === "spatial" ? (
            <div className="space-y-4">
              <AnalysisChildNav child="spatial" />
              <SpatialAnalyticsPanel />
            </div>
          ) : null}
          {waferModalView === "zones" ? (
            <div className="space-y-4">
              <AnalysisChildNav child="zones" />
              <EngineeringZonesPanel />
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
