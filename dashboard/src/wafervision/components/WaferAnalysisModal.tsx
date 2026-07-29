"use client";

import { useEffect, useMemo, useRef } from "react";
import { ArrowLeft, ChevronLeft, ChevronRight, X } from "lucide-react";
import { useAnalysis } from "@/wafervision/hooks/useAnalysis";
import { WaferAnalysisContent } from "@/wafervision/components/WaferAnalysisContent";
import { AnalysisChildNav } from "@/wafervision/components/AnalysisChildNav";
import {
  EngineeringZonesPanel,
  SpatialAnalyticsPanel,
} from "@/wafervision/components/SpatialAnalyticsPanel";
import { resolveLot } from "@/wafervision/utils/batchAggregates";
import { displayWaferName } from "@/wafervision/utils/format";
import { lotLabel } from "@/wafervision/utils/lotTaxonomy";
import { wafersInLot } from "@/wafervision/utils/batchAggregates";

export function WaferAnalysisModal() {
  const {
    isWaferModalOpen,
    closeWaferAnalysisModal,
    selected,
    selectedIndex,
    results,
    waferModalView,
    cycleLotWafer,
    activeTab,
  } = useAnalysis();
  const bodyRef = useRef<HTMLDivElement>(null);

  const lot = useMemo(() => {
    if (activeTab.startsWith("LOT_")) return activeTab;
    return selected ? resolveLot(selected) : "LOT_1";
  }, [activeTab, selected]);

  const members = useMemo(() => wafersInLot(results, lot), [results, lot]);
  const ordinal = members.findIndex((m) => m.index === selectedIndex) + 1;

  useEffect(() => {
    if (!isWaferModalOpen) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeWaferAnalysisModal();
    };
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener("keydown", onKey);
    };
  }, [isWaferModalOpen, closeWaferAnalysisModal]);

  useEffect(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = 0;
  }, [isWaferModalOpen, selectedIndex, waferModalView]);

  if (!isWaferModalOpen) return null;

  return (
    <div className="fixed inset-0 z-[60] flex justify-end">
      <button
        type="button"
        aria-label="Close backdrop"
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={closeWaferAnalysisModal}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Wafer Analysis"
        className="relative flex h-full w-full max-w-[1400px] flex-col border-l shadow-2xl"
        style={{ background: "var(--panel)", borderColor: "var(--line)" }}
      >
        <header
          className="sticky top-0 z-10 flex flex-wrap items-center gap-3 border-b px-4 py-3"
          style={{ background: "var(--panel)", borderColor: "var(--line)" }}
        >
          <button
            type="button"
            onClick={closeWaferAnalysisModal}
            className="inline-flex items-center gap-1 text-sm font-medium text-[#A78BFA] hover:text-[#7C3AED]"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to LOT
          </button>
          <div className="min-w-0 flex-1">
            <div className="text-sm font-semibold">{lotLabel(lot)}</div>
            <div className="truncate text-xs" style={{ color: "var(--muted)" }}>
              {selected ? displayWaferName(selected) : "—"}
            </div>
          </div>
          {members.length > 0 && (
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => cycleLotWafer(lot, -1)}
                className="rounded-lg border p-1.5"
                style={{ borderColor: "var(--line)" }}
                aria-label="Previous wafer"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <span className="font-mono text-xs">
                Wafer {Math.max(ordinal, 1)} / {members.length}
              </span>
              <button
                type="button"
                onClick={() => cycleLotWafer(lot, 1)}
                className="rounded-lg border p-1.5"
                style={{ borderColor: "var(--line)" }}
                aria-label="Next wafer"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          )}
          <button
            type="button"
            onClick={closeWaferAnalysisModal}
            className="rounded-lg border p-1.5"
            style={{ borderColor: "var(--line)" }}
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </header>

        <div ref={bodyRef} className="flex-1 overflow-y-auto p-4">
          {waferModalView === "analysis" && <WaferAnalysisContent />}
          {waferModalView === "spatial" && (
            <>
              <AnalysisChildNav leaf="Spatial Analytics" />
              <SpatialAnalyticsPanel />
            </>
          )}
          {waferModalView === "zones" && (
            <>
              <AnalysisChildNav leaf="Engineering Zone Analysis" />
              <EngineeringZonesPanel />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
