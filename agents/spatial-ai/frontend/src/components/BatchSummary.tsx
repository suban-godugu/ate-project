"use client";

import { useMemo } from "react";

import { useAnalysis } from "@/hooks/useAnalysis";
import { computeBatchSummary } from "@/utils/batchAggregates";
import { formatPercent } from "@/utils/format";

export function BatchSummary() {
  const { results } = useAnalysis();
  const stats = useMemo(() => computeBatchSummary(results), [results]);

  if (!results.length) {
    return (
      <section className="panel p-5">
        <h2 className="panel-title mb-2">Batch Summary</h2>
        <p className="text-sm text-[var(--muted)]">
          Analyze one or more wafers to populate lot-scale summary cards.
        </p>
      </section>
    );
  }

  const cards = [
    { label: "Total Wafers", value: String(stats.totalWafers) },
    { label: "Average Yield", value: formatPercent(stats.averageYield) },
    { label: "Highest Yield", value: formatPercent(stats.highestYield) },
    { label: "Lowest Yield", value: formatPercent(stats.lowestYield) },
    { label: "Average Confidence", value: formatPercent(stats.averageConfidence) },
    { label: "Total Good Dies", value: String(stats.totalGoodDies) },
    { label: "Total Fail Dies", value: String(stats.totalFailDies) },
    { label: "Total Dies", value: String(stats.totalDies) },
  ];

  return (
    <section className="panel p-5">
      <h2 className="panel-title mb-4">Batch Summary</h2>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-4">
        {cards.map((card) => (
          <div
            key={card.label}
            className="rounded-lg border border-[var(--line)] px-3 py-3"
          >
            <p className="text-[11px] uppercase tracking-[0.14em] text-[var(--muted)]">
              {card.label}
            </p>
            <p className="mt-1 font-mono text-lg font-semibold">{card.value}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
