"use client";

import { useMemo } from "react";

import { useAnalysis } from "@/hooks/useAnalysis";
import { computeLotSummary } from "@/utils/batchAggregates";
import { formatPercent } from "@/utils/format";

export function LotSummary() {
  const { results } = useAnalysis();
  const lots = useMemo(() => computeLotSummary(results), [results]);

  return (
    <section className="panel p-5">
      <h2 className="panel-title mb-2">LOT Summary</h2>
      <p className="mb-4 text-xs text-[var(--muted)]">
        Aggregate counts and average yields from session API results only.
      </p>
      {!results.length ? (
        <p className="text-sm text-[var(--muted)]">No wafers in session.</p>
      ) : (
        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
          {lots.map((bucket) => (
            <div
              key={bucket.lot}
              className="rounded-lg border border-[var(--line)] px-3 py-3"
            >
              <p className="font-mono text-sm font-semibold">{bucket.lot}</p>
              <p className="text-xs text-[var(--muted)]">↓</p>
              <p className="text-sm font-medium">{bucket.defect}</p>
              <div className="mt-2 flex justify-between text-xs text-[var(--muted)]">
                <span>{bucket.waferCount} Wafers</span>
                <span>Avg Yield {formatPercent(bucket.averageYield)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
