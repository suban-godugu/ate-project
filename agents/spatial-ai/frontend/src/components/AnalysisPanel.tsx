"use client";

import { useAnalysis } from "@/context/AnalysisContext";
import { displayLot, formatPercent } from "@/utils/format";

export function AnalysisPanel() {
  const { selected } = useAnalysis();
  if (!selected) {
    return (
      <section className="panel p-5">
        <h2 className="panel-title mb-2">Analysis Panel</h2>
        <p className="text-sm text-[var(--muted)]">No wafer selected.</p>
      </section>
    );
  }

  const gridSize = `${selected.grid_info?.rows ?? "—"} × ${selected.grid_info?.columns ?? "—"}`;

  return (
    <section className="panel p-5">
      <h2 className="panel-title mb-4">Analysis Panel</h2>
      <dl className="space-y-3 text-sm">
        <Row label="Defect Type" value={selected.classification?.defect_type || "—"} />
        <Row
          label="Confidence"
          value={formatPercent(selected.classification?.confidence)}
        />
        <Row label="Assigned LOT" value={displayLot(selected)} />
        <Row label="Grid Mode" value={selected.grid_info?.mode || "—"} />
        <Row label="Grid Size" value={gridSize} />
        <Row label="Yield" value={formatPercent(selected.yield_summary?.yield_percent)} />
      </dl>
    </section>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-[var(--line)] pb-2">
      <dt className="text-[var(--muted)]">{label}</dt>
      <dd className="font-mono font-medium">{value}</dd>
    </div>
  );
}

export function LotReferencePanel() {
  const lots = [
    ["LOT_1", "Center"],
    ["LOT_2", "Donut"],
    ["LOT_3", "Edge-Loc"],
    ["LOT_4", "Edge-Ring"],
    ["LOT_5", "Local"],
    ["LOT_6", "Near-Full"],
    ["LOT_7", "Normal"],
    ["LOT_8", "Random"],
    ["LOT_9", "Scratch"],
  ];

  return (
    <section className="panel p-5">
      <h2 className="panel-title mb-2">LOT Assignment</h2>
      <p className="mb-3 text-xs text-[var(--muted)]">
        Reference map (LOT_1–LOT_9). Live assignment is shown only from API fields.
      </p>
      <ul className="space-y-1.5 text-sm">
        {lots.map(([lot, defect]) => (
          <li
            key={lot}
            className="flex flex-col rounded-md border border-[var(--line)] px-3 py-2"
          >
            <span className="font-mono text-xs font-semibold">{lot}</span>
            <span className="text-[var(--muted)]">↓</span>
            <span>{defect}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
