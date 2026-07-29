"use client";

import { Fragment, memo, useMemo, useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import type { DetectedPattern } from "@/lib/api";
import { useVisualizationStore } from "@/stores/visualizationStore";
import { cn } from "@/lib/utils";

type Props = { patterns: DetectedPattern[] };

export const PatternAnalysisTable = memo(function PatternAnalysisTable({ patterns }: Props) {
  const expanded = useVisualizationStore((s) => s.expandedPatternRows);
  const toggle = useVisualizationStore((s) => s.togglePatternRow);
  const [search, setSearch] = useState("");

  const rows = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return patterns;
    return patterns.filter(
      (p) =>
        p.pattern_id.toLowerCase().includes(q) ||
        p.pattern_name.toLowerCase().includes(q) ||
        p.pattern_category.toLowerCase().includes(q),
    );
  }, [patterns, search]);

  if (!patterns.length) {
    return (
      <div className="glass-panel rounded-2xl p-6 text-sm text-[var(--muted)]" data-testid="pattern-table">
        Pattern analysis table populates from GET /patterns after detection completes.
      </div>
    );
  }

  return (
    <div className="glass-panel overflow-hidden rounded-2xl" data-testid="pattern-table">
      <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
          Pattern Analysis
        </h3>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search patterns…"
          className="rounded-lg border border-white/10 bg-black/25 px-3 py-1.5 text-xs"
        />
      </div>
      <div className="max-h-96 overflow-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-[var(--surface)]/95 text-xs uppercase text-[var(--muted)]">
            <tr>
              <th className="w-8 px-2 py-2" />
              <th className="px-3 py-2 text-left">Pattern ID</th>
              <th className="px-3 py-2 text-right">Occurrences</th>
              <th className="px-3 py-2 text-right">Confidence</th>
              <th className="px-3 py-2 text-left">Category</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((p) => {
              const open = expanded.has(p.id);
              return (
                <Fragment key={p.id}>
                  <tr
                    key={p.id}
                    className="border-t border-white/5 hover:bg-white/5"
                  >
                    <td className="px-2 py-2">
                      <button type="button" onClick={() => toggle(p.id)} aria-label="Expand">
                        {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                      </button>
                    </td>
                    <td className="px-3 py-2 font-mono text-xs">{p.pattern_id}</td>
                    <td className="px-3 py-2 text-right">{p.failure_count}</td>
                    <td className="px-3 py-2 text-right">
                      {(p.confidence * (p.confidence <= 1 ? 100 : 1)).toFixed(1)}%
                    </td>
                    <td className="px-3 py-2">{p.pattern_category}</td>
                  </tr>
                  {open && (
                    <tr className="bg-black/20 text-xs text-[var(--muted)]">
                      <td colSpan={5} className="px-4 py-2">
                        {p.pattern_name} · method {p.detection_method} · severity {p.severity_level} ·
                        affected dies {p.affected_die_count} · wafers {p.affected_wafer_count}
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
});
