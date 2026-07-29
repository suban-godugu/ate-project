"use client";

import { useAnalysis } from "@/wafervision/hooks/useAnalysis";
import {
  resolveConfidence,
  resolveDefect,
  resolveLot,
  resolveYield,
} from "@/wafervision/utils/batchAggregates";
import { formatPercent } from "@/wafervision/utils/format";

/** Per-wafer metadata definition list (not the full analysis tree). */
export function AnalysisPanel() {
  const { selected } = useAnalysis();

  if (!selected) {
    return (
      <section className="panel p-5">
        <h2 className="panel-title mb-3">Analysis</h2>
        <p className="text-sm" style={{ color: "var(--muted)" }}>
          No wafer selected.
        </p>
      </section>
    );
  }

  const grid = selected.grid_info;
  const rows = [
    { label: "Defect Type", value: resolveDefect(selected) },
    { label: "Confidence", value: formatPercent(resolveConfidence(selected)) },
    { label: "Assigned LOT", value: resolveLot(selected) },
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
    { label: "Yield", value: formatPercent(resolveYield(selected)) },
  ];

  return (
    <section className="panel p-5">
      <h2 className="panel-title mb-3">Analysis</h2>
      <dl className="space-y-2 text-sm">
        {rows.map((r) => (
          <div
            key={r.label}
            className="flex justify-between gap-4 border-b py-2"
            style={{ borderColor: "var(--line)" }}
          >
            <dt style={{ color: "var(--muted)" }}>{r.label}</dt>
            <dd className="font-mono font-medium">{r.value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
