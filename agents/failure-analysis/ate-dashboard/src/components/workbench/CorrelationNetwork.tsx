"use client";

import { memo, useMemo } from "react";
import type { CorrelationMetric } from "@/lib/api";
import { useVisualizationStore } from "@/stores/visualizationStore";

type Props = { correlations: CorrelationMetric[] };

export const CorrelationNetwork = memo(function CorrelationNetwork({
  correlations,
}: Props) {
  const selectedId = useVisualizationStore((s) => s.selectedCorrelationId);
  const setSelectedId = useVisualizationStore((s) => s.setSelectedCorrelationId);

  const nodes = useMemo(
    () =>
      correlations.slice(0, 24).map((c, i) => ({
        id: c.correlation_id,
        label: c.pattern_id,
        x: 40 + (i % 6) * 90,
        y: 40 + Math.floor(i / 6) * 70,
        weight: c.correlation_coefficient,
      })),
    [correlations],
  );

  const selected = correlations.find((c) => c.correlation_id === selectedId);

  if (!correlations.length) {
    return (
      <div className="glass-panel rounded-2xl p-6 text-sm text-[var(--muted)]" data-testid="correlation-network">
        Correlation network populates from GET /correlation after FA-FR-006 completes.
      </div>
    );
  }

  return (
    <div className="glass-panel grid gap-4 rounded-2xl p-4 lg:grid-cols-[1fr_280px]" data-testid="correlation-network">
      <div>
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
          Correlation Network
        </h3>
        <svg viewBox="0 0 560 280" className="h-64 w-full rounded-xl bg-black/25">
          {nodes.map((n) => (
            <g key={n.id}>
              <circle
                cx={n.x}
                cy={n.y}
                r={8 + n.weight * 10}
                fill={selectedId === n.id ? "#7C3AED" : "rgba(56,189,248,0.65)"}
                stroke="#fff"
                strokeWidth={selectedId === n.id ? 2 : 0}
                className="cursor-pointer"
                onClick={() => setSelectedId(n.id)}
              />
              <text x={n.x} y={n.y + 22} textAnchor="middle" fill="#94a3b8" fontSize="8">
                {n.label.slice(0, 10)}
              </text>
            </g>
          ))}
          {nodes.slice(0, -1).map((n, i) => {
            const next = nodes[i + 1];
            if (!next) return null;
            return (
              <line
                key={`${n.id}-${next.id}`}
                x1={n.x}
                y1={n.y}
                x2={next.x}
                y2={next.y}
                stroke="rgba(124,58,237,0.35)"
                strokeWidth={1 + n.weight}
              />
            );
          })}
        </svg>
      </div>
      <aside className="rounded-xl border border-white/10 bg-black/20 p-3 text-sm">
        <h4 className="text-xs uppercase tracking-wide text-[var(--muted)]">Details</h4>
        {selected ? (
          <dl className="mt-2 space-y-2 text-xs">
            <div>
              <dt className="text-[var(--muted)]">Pattern</dt>
              <dd>{selected.pattern_id}</dd>
            </div>
            <div>
              <dt className="text-[var(--muted)]">Fault</dt>
              <dd>{selected.fault_type}</dd>
            </div>
            <div>
              <dt className="text-[var(--muted)]">Coefficient</dt>
              <dd>{selected.correlation_coefficient.toFixed(3)}</dd>
            </div>
            <div>
              <dt className="text-[var(--muted)]">Confidence</dt>
              <dd>{(selected.confidence_score * 100).toFixed(1)}%</dd>
            </div>
            <div>
              <dt className="text-[var(--muted)]">Recommendation</dt>
              <dd>{selected.engineering_recommendation}</dd>
            </div>
          </dl>
        ) : (
          <p className="mt-2 text-xs text-[var(--muted)]">Click a node to inspect correlation details.</p>
        )}
      </aside>
    </div>
  );
});
