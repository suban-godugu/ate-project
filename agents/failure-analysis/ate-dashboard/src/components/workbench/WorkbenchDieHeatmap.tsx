"use client";

import { memo, useMemo } from "react";
import type { DieSummary } from "@/lib/api";
import { useVisualizationStore } from "@/stores/visualizationStore";
import { cn } from "@/lib/utils";

type Props = { dies: DieSummary[] };

function dedupeDiesByCoordinate(
  dies: Array<DieSummary & { x: number; y: number }>,
): Array<DieSummary & { x: number; y: number }> {
  const byCoord = new Map<string, DieSummary & { x: number; y: number }>();
  for (const die of dies) {
    const coordKey = `${die.x},${die.y}`;
    const existing = byCoord.get(coordKey);
    if (
      !existing ||
      die.is_failing ||
      die.failure_count > existing.failure_count
    ) {
      byCoord.set(coordKey, die);
    }
  }
  return Array.from(byCoord.values());
}

function dieCellKey(die: DieSummary & { x: number; y: number }): string {
  return `${die.x},${die.y}`;
}

export const WorkbenchDieHeatmap = memo(function WorkbenchDieHeatmap({ dies }: Props) {
  const selectedDie = useVisualizationStore((s) => s.selectedDie);
  const setSelectedDie = useVisualizationStore((s) => s.setSelectedDie);

  const grid = useMemo(() => {
    const withCoords = dies.filter(
      (d) => typeof d.x === "number" && typeof d.y === "number",
    ) as Array<DieSummary & { x: number; y: number }>;
    if (!withCoords.length) return { cells: [], minX: 0, minY: 0, maxX: 0, maxY: 0 };
    const xs = withCoords.map((d) => d.x);
    const ys = withCoords.map((d) => d.y);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    const cells = dedupeDiesByCoordinate(withCoords);
    return { cells, minX, maxX, minY, maxY };
  }, [dies]);

  if (!grid.cells.length) {
    return (
      <div className="glass-panel rounded-2xl p-6 text-sm text-[var(--muted)]" data-testid="die-heatmap">
        No die-level coordinates returned from backend analysis.
      </div>
    );
  }

  const cols = grid.maxX - grid.minX + 1;
  const rows = grid.maxY - grid.minY + 1;

  return (
    <div className="glass-panel rounded-2xl p-4" data-testid="die-heatmap">
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
        Die Heatmap Grid
      </h3>
      <div
        className="grid gap-0.5 overflow-auto rounded-xl border border-white/10 bg-black/25 p-2"
        style={{
          gridTemplateColumns: `repeat(${Math.min(cols, 32)}, minmax(14px, 1fr))`,
        }}
      >
        {grid.cells.map((die) => {
          const selected =
            selectedDie?.x === die.x &&
            selectedDie?.y === die.y;
          return (
            <button
              key={dieCellKey(die)}
              type="button"
              title={`${die.die_id} · failures ${die.failure_count}`}
              onClick={() =>
                setSelectedDie({
                  die_id: die.die_id,
                  x: die.x,
                  y: die.y,
                  status: die.is_failing ? "fail" : "pass",
                  failure_count: die.failure_count,
                  confidence: die.health_score,
                })
              }
              className={cn(
                "aspect-square rounded-sm text-[0px]",
                die.is_failing ? "bg-[var(--danger)]/70" : "bg-[var(--success)]/40",
                selected && "ring-2 ring-white",
              )}
            />
          );
        })}
      </div>
      {selectedDie && (
        <dl className="mt-3 grid grid-cols-2 gap-2 text-xs">
          <div>
            <dt className="text-[var(--muted)]">Die</dt>
            <dd>{selectedDie.die_id}</dd>
          </div>
          <div>
            <dt className="text-[var(--muted)]">Coords</dt>
            <dd>
              ({selectedDie.x}, {selectedDie.y})
            </dd>
          </div>
          <div>
            <dt className="text-[var(--muted)]">Failures</dt>
            <dd>{selectedDie.failure_count ?? 0}</dd>
          </div>
          <div>
            <dt className="text-[var(--muted)]">Confidence</dt>
            <dd>{Number(selectedDie.confidence ?? 0).toFixed(2)}</dd>
          </div>
        </dl>
      )}
      <p className="mt-2 text-xs text-[var(--muted)]">
        Grid {cols}×{rows} · {grid.cells.length} dies from backend
      </p>
    </div>
  );
});
