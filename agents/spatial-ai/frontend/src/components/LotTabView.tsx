"use client";

import { useMemo } from "react";

import { useAnalysis } from "@/hooks/useAnalysis";
import type { LotDashboardTab } from "@/types/wafer";
import { wafersInLot } from "@/utils/batchAggregates";
import { defectFromLotCode } from "@/utils/lotTaxonomy";
import {
  cn,
  formatPercent,
  readDefectType,
  readWaferName,
  toDataUrl,
} from "@/utils/format";

/**
 * LOT tab: wafer card grid only.
 * Selecting a card opens the Wafer Analysis modal (does not scroll inline).
 */
export function LotTabView({ lot }: { lot: LotDashboardTab }) {
  const {
    results,
    selectedIndex,
    openWaferAnalysisModal,
  } = useAnalysis();
  const members = useMemo(() => wafersInLot(results, lot), [results, lot]);
  const defect = defectFromLotCode(lot) ?? "—";

  return (
    <div className="space-y-4">
      <section className="panel p-5">
        <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="panel-title">{lot}</h2>
            <p className="mt-1 text-sm text-[var(--muted)]">
              {defect} · {members.length} wafer{members.length === 1 ? "" : "s"} in
              session
            </p>
          </div>
        </div>

        {members.length === 0 ? (
          <p className="text-sm text-[var(--muted)]">
            No wafers assigned to {lot} in the current session. Analyze wafers to
            populate this LOT.
          </p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {members.map(({ wafer, index }) => {
              const thumb = toDataUrl(wafer.images?.original);
              const highlighted = index === selectedIndex;
              return (
                <button
                  key={`${wafer.wafer_id}-${index}`}
                  type="button"
                  onClick={() => openWaferAnalysisModal(index)}
                  className={cn(
                    "rounded-lg border px-3 py-3 text-left transition",
                    highlighted
                      ? "border-ink-800 bg-ink-800/5 dark:border-ink-200 dark:bg-ink-200/10"
                      : "border-[var(--line)] hover:border-ink-400 dark:hover:border-ink-500",
                  )}
                >
                  <div className="mb-3 flex aspect-square items-center justify-center rounded border border-[var(--line)] bg-ink-950/5 p-2 dark:bg-black/20">
                    {thumb ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={thumb}
                        alt={readWaferName(wafer)}
                        className="max-h-full max-w-full object-contain"
                      />
                    ) : (
                      <span className="text-[10px] text-[var(--muted)]">No image</span>
                    )}
                  </div>
                  <p className="truncate font-mono text-xs font-semibold">
                    {readWaferName(wafer)}
                  </p>
                  <dl className="mt-2 grid grid-cols-2 gap-x-2 gap-y-1 text-[11px]">
                    <dt className="text-[var(--muted)]">Yield</dt>
                    <dd className="font-mono text-right">
                      {formatPercent(wafer.yield_summary?.yield_percent)}
                    </dd>
                    <dt className="text-[var(--muted)]">Confidence</dt>
                    <dd className="font-mono text-right">
                      {formatPercent(wafer.classification?.confidence)}
                    </dd>
                    <dt className="text-[var(--muted)]">Prediction</dt>
                    <dd className="truncate text-right">{readDefectType(wafer)}</dd>
                    <dt className="text-[var(--muted)]">Status</dt>
                    <dd className="text-right text-signal-pass">Analyzed</dd>
                  </dl>
                </button>
              );
            })}
          </div>
        )}
      </section>

      {members.length > 0 ? (
        <p className="text-sm text-[var(--muted)]">
          Select a wafer card to open Wafer Analysis for {lot}.
        </p>
      ) : null}
    </div>
  );
}
