"use client";

import { useMemo } from "react";

import { useAnalysis } from "@/hooks/useAnalysis";
import { filterAndSortWafers } from "@/utils/batchAggregates";
import {
  cn,
  displayLot,
  formatPercent,
  readDefectType,
  readWaferName,
} from "@/utils/format";

/**
 * Compact wafer results browser for the main workspace.
 * Filter controls live in WaferFilterToolbar; this list preserves selection behaviour.
 */
export function WaferResultsStrip() {
  const {
    results,
    selectedIndex,
    selectWafer,
    filters,
    comparisonIndices,
    toggleComparison,
  } = useAnalysis();

  const filtered = useMemo(
    () => filterAndSortWafers(results, filters),
    [results, filters],
  );

  if (results.length === 0) {
    return null;
  }

  return (
    <section className="panel p-4">
      <h2 className="panel-title mb-3">Wafer Results</h2>
      <div className="max-h-[240px] overflow-auto">
        <ul className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
          {filtered.map(({ wafer, index }) => {
            const active = index === selectedIndex;
            const compared = comparisonIndices.includes(index);
            return (
              <li key={`${wafer.wafer_id}-${index}`}>
                <div
                  className={cn(
                    "rounded-lg border px-3 py-2 transition",
                    active
                      ? "border-signal-info bg-signal-info/10"
                      : "border-[var(--line)] hover:border-ink-400",
                  )}
                >
                  <div className="flex items-start gap-2">
                    <input
                      type="checkbox"
                      checked={compared}
                      onChange={() => toggleComparison(index)}
                      title="Add to comparison"
                      className="mt-1"
                    />
                    <button
                      type="button"
                      onClick={() => selectWafer(index)}
                      className="min-w-0 flex-1 text-left"
                    >
                      <p className="truncate font-mono text-xs">
                        {readWaferName(wafer)}
                      </p>
                      <p className="mt-0.5 text-sm font-medium">
                        {readDefectType(wafer)}
                      </p>
                      <div className="mt-1.5 flex flex-wrap gap-x-2 gap-y-0.5 text-[11px] text-[var(--muted)]">
                        <span>LOT {displayLot(wafer)}</span>
                        <span>
                          Yield {formatPercent(wafer.yield_summary?.yield_percent)}
                        </span>
                        <span>
                          Conf {formatPercent(wafer.classification?.confidence)}
                        </span>
                        <span className="font-semibold text-signal-good">
                          Analyzed
                        </span>
                      </div>
                    </button>
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}
