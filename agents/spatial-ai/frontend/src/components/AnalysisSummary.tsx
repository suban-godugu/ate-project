"use client";

import { useMemo } from "react";

import { useAnalysis } from "@/context/AnalysisContext";
import { countWafersInLot } from "@/utils/batchAggregates";
import { displayLot, formatPercent } from "@/utils/format";

function Card({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-[var(--line)] bg-[color-mix(in_srgb,var(--panel)_88%,#d7e2ef)] px-3 py-3 dark:bg-ink-900/40">
      <p className="text-[11px] uppercase tracking-[0.14em] text-[var(--muted)]">{label}</p>
      <p className="mt-1 truncate font-mono text-sm font-semibold">{value}</p>
    </div>
  );
}

export function AnalysisSummary() {
  const { selected, results, isAnalyzing } = useAnalysis();

  const wafersInThisLot = useMemo(() => {
    if (!selected) return 0;
    const lot = displayLot(selected);
    if (!lot || lot === "—") return 0;
    return countWafersInLot(results, lot);
  }, [selected, results]);

  if (isAnalyzing && !selected) {
    return (
      <section className="panel p-5">
        <h2 className="panel-title mb-4">Summary</h2>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
          {Array.from({ length: 10 }).map((_, index) => (
            <div key={index} className="skeleton h-16" />
          ))}
        </div>
      </section>
    );
  }

  if (!selected) {
    return (
      <section className="panel p-5">
        <h2 className="panel-title mb-2">Summary</h2>
        <p className="text-sm text-[var(--muted)]">
          Upload and analyze a wafer to populate engineering summary cards.
        </p>
      </section>
    );
  }

  const gridSize =
    selected.grid_info?.rows != null
      ? `${selected.grid_info.rows} × ${selected.grid_info.columns}`
      : "—";

  return (
    <section className="panel p-5">
      <h2 className="panel-title mb-4">Summary Cards</h2>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
        <Card label="Defect Type" value={selected.classification?.defect_type || "—"} />
        <Card
          label="Confidence"
          value={formatPercent(selected.classification?.confidence)}
        />
        <Card label="Assigned LOT" value={displayLot(selected)} />
        <Card label="Yield" value={formatPercent(selected.yield_summary?.yield_percent)} />
        <Card
          label="Good Dies"
          value={String(selected.yield_summary?.good_dies ?? "—")}
        />
        <Card
          label="Fail Dies"
          value={String(selected.yield_summary?.fail_dies ?? "—")}
        />
        <Card
          label="Total Dies"
          value={String(selected.yield_summary?.total_dies ?? "—")}
        />
        <Card label="Grid Mode" value={selected.grid_info?.mode || "—"} />
        <Card label="Grid Size" value={gridSize} />
        <Card label="Total Wafers In This LOT" value={String(wafersInThisLot)} />
      </div>
    </section>
  );
}
