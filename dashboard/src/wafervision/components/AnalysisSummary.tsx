"use client";

import { useAnalysis } from "@/wafervision/hooks/useAnalysis";
import {
  resolveConfidence,
  resolveDefect,
  resolveFailDies,
  resolveGoodDies,
  resolveLot,
  resolveTotalDies,
  resolveYield,
  wafersInLot,
} from "@/wafervision/utils/batchAggregates";
import { formatNumber, formatPercent } from "@/wafervision/utils/format";

export function AnalysisSummary() {
  const { selected, results, isAnalyzing } = useAnalysis();

  if (!selected) {
    if (isAnalyzing) {
      return (
        <section className="panel p-5">
          <h2 className="panel-title mb-3">Summary Cards</h2>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
            {Array.from({ length: 10 }).map((_, i) => (
              <div key={i} className="skeleton h-16" />
            ))}
          </div>
        </section>
      );
    }
    return (
      <section className="panel p-5">
        <h2 className="panel-title mb-3">Summary Cards</h2>
        <p className="text-sm" style={{ color: "var(--muted)" }}>
          Upload and analyze a wafer to populate engineering summary cards.
        </p>
      </section>
    );
  }

  const lot = resolveLot(selected);
  const lotCount = wafersInLot(results, lot).length;
  const grid = selected.grid_info;
  const cards = [
    { label: "Defect Type", value: resolveDefect(selected) },
    { label: "Confidence", value: formatPercent(resolveConfidence(selected)) },
    { label: "Assigned LOT", value: lot },
    { label: "Yield", value: formatPercent(resolveYield(selected)) },
    { label: "Good Dies", value: formatNumber(resolveGoodDies(selected)) },
    { label: "Fail Dies", value: formatNumber(resolveFailDies(selected)) },
    { label: "Total Dies", value: formatNumber(resolveTotalDies(selected)) },
    { label: "Grid Mode", value: grid?.mode ?? "—" },
    {
      label: "Grid Size",
      value:
        grid?.rows != null && grid?.columns != null
          ? `${grid.rows} × ${grid.columns}`
          : grid?.size != null
            ? String(grid.size)
            : "—",
    },
    { label: "Total Wafers In This LOT", value: String(lotCount) },
  ];

  return (
    <section className="panel p-5">
      <h2 className="panel-title mb-3">Summary Cards</h2>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
        {cards.map((c) => (
          <div key={c.label} className="rounded-lg border p-3" style={{ borderColor: "var(--line)" }}>
            <div className="text-[11px] uppercase tracking-wide" style={{ color: "var(--muted)" }}>
              {c.label}
            </div>
            <div className="mt-1 font-mono text-base font-semibold">{c.value}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
