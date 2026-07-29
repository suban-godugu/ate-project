"use client";

import type { ExecutiveSummaryCard, ScanDebugKpiId } from "@/types/kpiDrillDown";
import { normalizeKpiId } from "@/store/uiStore";

export function ExecutiveSummary({
  cards,
  onCardClick,
}: {
  cards: ExecutiveSummaryCard[];
  onCardClick?: (kpiId: ScanDebugKpiId) => void;
}) {
  if (!cards?.length) {
    return (
      <section className="glass-card gradient-border p-5">
        <div className="text-sm text-muted">Loading executive summary…</div>
      </section>
    );
  }

  return (
    <section
      id="ai-executive-summary"
      aria-label="AI Executive Summary"
      className="glass-card gradient-border p-5 ring-1 ring-success/10"
    >
      <div className="mb-5 border-b border-border/60 pb-3">
        <div className="text-[10px] uppercase tracking-[0.18em] text-success/80">AI Executive Summary</div>
        <h2 className="mt-1 font-display text-lg font-semibold text-white">Debug Recommendation Impact</h2>
        <p className="mt-1 text-xs text-muted">Nine KPI cards summarizing broken chains, timing, power, constraints, and AI confidence.</p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {cards.map((c, idx) => (
          <button
            key={`${c.id}-${c.label}-${idx}`}
            type="button"
            title={c.detail}
            onClick={() => {
              const kpi = normalizeKpiId(c.id);
              if (kpi) onCardClick?.(kpi);
            }}
            className="group flex min-h-[96px] flex-col items-center justify-center rounded-xl border border-border/70 bg-[#0c1018] px-4 py-5 text-center transition hover:border-success/35 hover:bg-success/[0.03]"
          >
            <div className="text-[10px] font-medium uppercase tracking-[0.16em] text-slate-500 group-hover:text-slate-400">
              {c.label}
            </div>
            <div className="mt-2 font-display text-3xl font-semibold leading-none text-success">
              {c.value}
            </div>
          </button>
        ))}
      </div>
    </section>
  );
}
