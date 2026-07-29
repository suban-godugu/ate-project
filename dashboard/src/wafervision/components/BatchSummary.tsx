"use client";

import { useMemo } from "react";
import { useAnalysis } from "@/wafervision/hooks/useAnalysis";
import { batchSummary } from "@/wafervision/utils/batchAggregates";
import { formatNumber, formatPercent } from "@/wafervision/utils/format";

export function BatchSummary() {
  const { results } = useAnalysis();
  const s = useMemo(() => batchSummary(results), [results]);

  const cards = [
    { label: "Total Wafers", value: formatNumber(s.totalWafers) },
    { label: "Average Yield", value: formatPercent(s.averageYield) },
    { label: "Highest Yield", value: formatPercent(s.highestYield) },
    { label: "Lowest Yield", value: formatPercent(s.lowestYield) },
    { label: "Average Confidence", value: formatPercent(s.averageConfidence) },
    { label: "Total Good Dies", value: formatNumber(s.totalGoodDies) },
    { label: "Total Fail Dies", value: formatNumber(s.totalFailDies) },
    { label: "Total Dies", value: formatNumber(s.totalDies) },
  ];

  return (
    <section className="panel p-5">
      <h2 className="panel-title mb-3">Batch Summary</h2>
      {!results.length ? (
        <p className="text-sm text-[var(--muted)]">
          Analyze one or more wafers to populate lot-scale summary cards.
        </p>
      ) : (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-4">
          {cards.map(({ label, value }) => (
              <div
                key={label}
                className="rounded-xl border border-[#2D3748] bg-[#0c1220]/60 p-4"
              >
              <p className="text-[11px] font-medium uppercase tracking-wide text-[var(--muted)]">
                {label}
              </p>
              <p className="mt-2 font-mono text-xl font-semibold text-[var(--text)]">{value}</p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
