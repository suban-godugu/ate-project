"use client";

import { useMemo, useState } from "react";
import type { RecommendationRow } from "@/types/kpiDrillDown";
import { ACTION_LABELS } from "@/lib/kpiDrillDown/actionLabels";
import { confidenceColor } from "@/lib/kpiDrillDown/kpiDrillDownUtils";

const CATEGORY_BADGE: Record<string, string> = {
  "Broken Chain": "border-primary/40 bg-primary/15 text-primary",
  Timing: "border-warning/40 bg-warning/15 text-warning",
  Power: "border-danger/40 bg-danger/15 text-danger",
  "ATPG Constraint": "border-sky-400/40 bg-sky-400/15 text-sky-300",
  "Physical Defect": "border-success/40 bg-success/15 text-success",
};

const PRIORITY_BADGE: Record<string, string> = {
  Critical: "border-danger/40 bg-danger/15 text-danger",
  High: "border-warning/40 bg-warning/15 text-warning",
  Medium: "border-primary/40 bg-primary/15 text-primary",
  Low: "border-border bg-white/5 text-slate-300",
};

export function RecommendationTable({ rows }: { rows: RecommendationRow[] }) {
  const [query, setQuery] = useState("");
  const safeRows = rows ?? [];

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return safeRows;
    return safeRows.filter((r) =>
      [
        r.id,
        r.categoryLabel,
        r.scanChain,
        r.rootCause,
        r.recommendation,
        r.actionLabel,
        r.affectedScanChain,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q)
    );
  }, [query, safeRows]);

  return (
    <section className="glass-card gradient-border overflow-hidden">
      <div className="border-b border-border/70 px-4 py-4">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">
          Scan Debug Recommendations
        </div>
        <h2 className="font-display text-xl font-semibold text-white">Top Scan Debug Recommendations</h2>
        <p className="mt-1 text-sm text-muted">
          Priority debug actions ranked by AI confidence and impact — what to work on and where.
        </p>
      </div>

      <div className="border-b border-border/70 px-4 py-3">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search recommendations, scan chains, root causes…"
          className="w-full max-w-md rounded-xl border border-border bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-primary/50"
        />
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-white/5 text-[11px] uppercase tracking-wide text-slate-400">
            <tr>
              {[
                "Recommendation ID",
                "Category",
                "Scan Chain",
                "Root Cause",
                "Recommendation",
                "Priority",
                "Confidence",
                "Expected Impact",
              ].map((h) => (
                <th key={h} className="whitespace-nowrap px-3 py-3 font-medium">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((r) => {
              const category = r.categoryLabel ?? ACTION_LABELS[r.category];
              const priority = r.priorityLabel ?? r.priority;
              return (
                <tr key={r.id} className="border-t border-border/50 hover:bg-white/[0.03]">
                  <td className="px-3 py-3 font-medium text-primary">{r.id}</td>
                  <td className="px-3 py-3">
                    <span
                      className={`rounded-full border px-2 py-0.5 text-xs ${CATEGORY_BADGE[category] ?? "border-border text-slate-300"}`}
                    >
                      {category}
                    </span>
                  </td>
                  <td className="px-3 py-3 text-slate-200">{r.scanChain ?? r.affectedScanChain}</td>
                  <td className="px-3 py-3 text-slate-300">{r.rootCause ?? "—"}</td>
                  <td className="px-3 py-3 font-medium text-white">
                    {r.recommendation ?? r.actionLabel ?? ACTION_LABELS[r.category]}
                  </td>
                  <td className="px-3 py-3">
                    <span
                      className={`rounded-full border px-2 py-0.5 text-xs ${PRIORITY_BADGE[priority] ?? "border-border text-slate-300"}`}
                    >
                      {priority}
                    </span>
                  </td>
                  <td className={`px-3 py-3 font-medium ${confidenceColor(r.confidence ?? 0)}`}>
                    {Math.round((r.confidence ?? 0) * 100)}%
                  </td>
                  <td className="px-3 py-3 text-success">{r.expectedImpact ?? `+${r.expectedYieldGainPct}% yield`}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="border-t border-border/70 px-4 py-3 text-xs text-muted">
        Showing {filtered.length} of {safeRows.length} recommendations
      </div>
    </section>
  );
}
