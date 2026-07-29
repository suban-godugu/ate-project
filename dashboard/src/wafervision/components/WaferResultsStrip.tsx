"use client";

import { useAnalysis } from "@/wafervision/hooks/useAnalysis";
import {
  filterAndSortWafers,
  resolveConfidence,
  resolveDefect,
  resolveLot,
  resolveYield,
} from "@/wafervision/utils/batchAggregates";
import { displayWaferName, formatPercent, cn } from "@/wafervision/utils/format";

export function WaferResultsStrip() {
  const { results, filters, selectedIndex, selectWafer, comparisonIndices, toggleComparison } =
    useAnalysis();

  if (!results.length) return null;

  const filtered = filterAndSortWafers(results, filters);

  return (
    <section className="panel p-4">
      <h2 className="panel-title mb-3">Wafer results</h2>
      <div className="flex gap-3 overflow-x-auto pb-1">
        {filtered.map(({ index, result }) => {
          const selected = index === selectedIndex;
          const compared = comparisonIndices.includes(index);
          return (
            <div
              key={index}
              className={cn(
                "min-w-[200px] shrink-0 rounded-lg border p-3 transition cursor-pointer",
                selected ? "border-[#7C3AED] bg-[#7C3AED]/10 ring-1 ring-[#7C3AED]/50" : "border-[#2D3748]",
                "hover:border-[#7C3AED]/50"
              )}
              onClick={() => selectWafer(index)}
              onKeyDown={(e) => e.key === "Enter" && selectWafer(index)}
              role="button"
              tabIndex={0}
            >
              <div className="mb-2 flex items-start justify-between gap-2">
                <span className="truncate text-sm font-medium text-[var(--text)]">
                  {displayWaferName(result)}
                </span>
                <label
                  className="flex shrink-0 items-center gap-1 text-xs text-[var(--muted)]"
                  onClick={(e) => e.stopPropagation()}
                >
                  <input
                    type="checkbox"
                    checked={compared}
                    onChange={() => toggleComparison(index)}
                  />
                  Compare
                </label>
              </div>
              <dl className="grid grid-cols-2 gap-x-2 gap-y-1 text-xs">
                <dt className="text-[var(--muted)]">Defect</dt>
                <dd className="text-[var(--text)]">{resolveDefect(result)}</dd>
                <dt className="text-[var(--muted)]">LOT</dt>
                <dd className="text-[var(--text)]">{resolveLot(result)}</dd>
                <dt className="text-[var(--muted)]">Yield</dt>
                <dd className="text-[var(--text)]">{formatPercent(resolveYield(result))}</dd>
                <dt className="text-[var(--muted)]">Conf</dt>
                <dd className="text-[var(--text)]">{formatPercent(resolveConfidence(result))}</dd>
              </dl>
            </div>
          );
        })}
      </div>
    </section>
  );
}
