"use client";

import { useAnalysis } from "@/wafervision/hooks/useAnalysis";
import {
  resolveConfidence,
  resolveDefect,
  resolveYield,
  wafersInLot,
} from "@/wafervision/utils/batchAggregates";
import { displayWaferName, formatPercent, toDataUrl, cn } from "@/wafervision/utils/format";
import { lotLabel, lotToDefect } from "@/wafervision/utils/lotTaxonomy";

interface LotTabViewProps {
  lot: string;
}

export function LotTabView({ lot }: LotTabViewProps) {
  const { results, selectedIndex, openWaferAnalysisModal } = useAnalysis();
  const members = wafersInLot(results, lot);
  const defect = lotToDefect(lot);

  return (
    <section className="panel p-5 space-y-4">
      <div>
        <h2 className="panel-title">{lot}</h2>
        <p className="mt-1 text-sm" style={{ color: "var(--muted)" }}>
          {defect ?? "—"} · {members.length} wafer{members.length === 1 ? "" : "s"} in session
        </p>
      </div>

      {members.length === 0 ? (
        <p className="text-sm" style={{ color: "var(--muted)" }}>
          No wafers assigned to {lot} in the current session. Analyze wafers to populate this LOT.
        </p>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {members.map(({ index, result }) => {
              const thumb = toDataUrl(result.images?.original);
              const selected = index === selectedIndex;
              return (
                <button
                  key={index}
                  type="button"
                  onClick={() => openWaferAnalysisModal(index)}
                  className={cn(
                    "rounded-xl border p-3 text-left transition",
                    selected
                      ? "border-[#7C3AED] bg-[#7C3AED]/10"
                      : "border-[#2D3748] hover:border-[#7C3AED]/50"
                  )}
                >
                  <div className="mb-3 aspect-square overflow-hidden rounded-lg bg-[#0c1220]">
                    {thumb ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={thumb} alt="" className="h-full w-full object-contain" />
                    ) : (
                      <div
                        className="flex h-full items-center justify-center text-xs"
                        style={{ color: "var(--muted)" }}
                      >
                        No image
                      </div>
                    )}
                  </div>
                  <div className="truncate text-sm font-medium">{displayWaferName(result)}</div>
                  <div className="mt-1 grid grid-cols-2 gap-1 text-xs" style={{ color: "var(--muted)" }}>
                    <span>Yield {formatPercent(resolveYield(result))}</span>
                    <span>Conf {formatPercent(resolveConfidence(result))}</span>
                    <span>Prediction {resolveDefect(result)}</span>
                    <span className="text-signal-good">Analyzed</span>
                  </div>
                </button>
              );
            })}
          </div>
          <p className="text-xs" style={{ color: "var(--muted)" }}>
            Select a wafer card to open Wafer Analysis for {lotLabel(lot)}.
          </p>
        </>
      )}
    </section>
  );
}
