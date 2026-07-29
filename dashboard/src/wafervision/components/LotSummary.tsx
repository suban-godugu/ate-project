"use client";

import { useMemo } from "react";
import { ArrowDown } from "lucide-react";
import type { DashboardTab } from "@/wafervision/types";
import { useAnalysis } from "@/wafervision/hooks/useAnalysis";
import { lotSummary } from "@/wafervision/utils/batchAggregates";
import { formatPercent } from "@/wafervision/utils/format";

export function LotSummary() {
  const { results, setActiveTab } = useAnalysis();
  const lots = useMemo(() => lotSummary(results), [results]);

  return (
    <section className="panel p-5">
      <h2 className="panel-title mb-1">LOT Summary</h2>
      <p className="mb-4 text-xs text-[var(--muted)]">
        Aggregates session API results only across the fixed nine-LOT taxonomy.
      </p>
      {!results.length ? (
        <p className="text-sm text-[var(--muted)]">No wafers in session.</p>
      ) : (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {lots.map(({ lot, defect, count, avgYield }) => (
            <button
              key={lot}
              type="button"
              onClick={() => setActiveTab(lot as DashboardTab)}
              className="rounded-xl border border-[#2D3748] bg-[#0c1220]/60 p-4 text-left transition hover:border-[#7C3AED]/50 hover:bg-[#7C3AED]/5"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="font-mono text-sm font-semibold text-[var(--text)]">{lot}</div>
                  <div className="mt-1 flex items-center gap-1 text-xs text-[var(--muted)]">
                    <ArrowDown className="h-3 w-3" />
                    {defect}
                  </div>
                </div>
                <span className="rounded-full bg-[#7C3AED]/20 px-2 py-0.5 font-mono text-xs text-[#A78BFA]">
                  {count}
                </span>
              </div>
              <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
                <div>
                  <dt className="text-[11px] uppercase text-[var(--muted)]">Wafers</dt>
                  <dd className="font-mono font-medium">{count}</dd>
                </div>
                <div>
                  <dt className="text-[11px] uppercase text-[var(--muted)]">Avg Yield</dt>
                  <dd className="font-mono font-medium">{formatPercent(avgYield)}</dd>
                </div>
              </dl>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}
