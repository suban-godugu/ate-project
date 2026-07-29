"use client";

import { useMemo, useRef, useState } from "react";

import { useAnalysis } from "@/hooks/useAnalysis";
import {
  filterAndSortWafers,
  type WaferSortKey,
} from "@/utils/batchAggregates";
import {
  cn,
  displayLot,
  formatPercent,
  readDefectType,
  readWaferName,
} from "@/utils/format";
import { DEFECT_CLASSES, LOT_TAXONOMY } from "@/utils/lotTaxonomy";

const ROW_HEIGHT = 96;
const VISIBLE_ROWS = 8;

export function WaferSidebar() {
  const {
    results,
    selectedIndex,
    selectWafer,
    filters,
    setFilters,
    comparisonIndices,
    toggleComparison,
  } = useAnalysis();

  const filtered = useMemo(
    () => filterAndSortWafers(results, filters),
    [results, filters],
  );

  const scrollRef = useRef<HTMLDivElement>(null);
  const [scrollTop, setScrollTop] = useState(0);

  const start = Math.max(0, Math.floor(scrollTop / ROW_HEIGHT) - 2);
  const end = Math.min(filtered.length, start + VISIBLE_ROWS + 4);
  const windowed = filtered.slice(start, end);
  const topPad = start * ROW_HEIGHT;
  const bottomPad = Math.max(0, (filtered.length - end) * ROW_HEIGHT);

  return (
    <aside className="panel p-4">
      <h2 className="panel-title mb-3">Wafer Sidebar</h2>

      {results.length === 0 ? (
        <p className="text-sm text-[var(--muted)]">
          Batch / single results appear here after analysis.
        </p>
      ) : (
        <>
          <div className="mb-3 space-y-2">
            <input
              type="search"
              placeholder="Search name · defect · LOT · yield"
              value={filters.search}
              onChange={(e) => setFilters({ search: e.target.value })}
              className="w-full rounded-lg border border-[var(--line)] bg-transparent px-3 py-2 text-xs outline-none focus:border-signal-info"
            />

            <div className="grid grid-cols-2 gap-2">
              <select
                value={filters.defectFilter}
                onChange={(e) => setFilters({ defectFilter: e.target.value })}
                className="rounded-lg border border-[var(--line)] bg-transparent px-2 py-1.5 text-xs"
              >
                <option value="All">All Defects</option>
                {DEFECT_CLASSES.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
              <select
                value={filters.lotFilter}
                onChange={(e) => setFilters({ lotFilter: e.target.value })}
                className="rounded-lg border border-[var(--line)] bg-transparent px-2 py-1.5 text-xs"
              >
                <option value="All">All LOTs</option>
                {LOT_TAXONOMY.map(({ lot }) => (
                  <option key={lot} value={lot}>
                    {lot}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-3 gap-2">
              <input
                type="number"
                placeholder="Yield min"
                value={filters.yieldMin ?? ""}
                onChange={(e) =>
                  setFilters({
                    yieldMin: e.target.value === "" ? null : Number(e.target.value),
                  })
                }
                className="rounded-lg border border-[var(--line)] bg-transparent px-2 py-1.5 text-xs"
              />
              <input
                type="number"
                placeholder="Yield max"
                value={filters.yieldMax ?? ""}
                onChange={(e) =>
                  setFilters({
                    yieldMax: e.target.value === "" ? null : Number(e.target.value),
                  })
                }
                className="rounded-lg border border-[var(--line)] bg-transparent px-2 py-1.5 text-xs"
              />
              <input
                type="number"
                placeholder="Conf min"
                value={filters.confidenceMin ?? ""}
                onChange={(e) =>
                  setFilters({
                    confidenceMin:
                      e.target.value === "" ? null : Number(e.target.value),
                  })
                }
                className="rounded-lg border border-[var(--line)] bg-transparent px-2 py-1.5 text-xs"
              />
            </div>

            <div className="flex gap-2">
              <select
                value={filters.sortKey}
                onChange={(e) =>
                  setFilters({ sortKey: e.target.value as WaferSortKey })
                }
                className="flex-1 rounded-lg border border-[var(--line)] bg-transparent px-2 py-1.5 text-xs"
              >
                <option value="name">Sort: Name</option>
                <option value="yield">Sort: Yield</option>
                <option value="confidence">Sort: Confidence</option>
                <option value="lot">Sort: LOT</option>
                <option value="defect">Sort: Defect</option>
                <option value="fail_dies">Sort: Fail Dies</option>
                <option value="good_dies">Sort: Good Dies</option>
              </select>
              <button
                type="button"
                onClick={() => setFilters({ sortAsc: !filters.sortAsc })}
                className="rounded-lg border border-[var(--line)] px-2 py-1.5 text-xs"
              >
                {filters.sortAsc ? "Asc" : "Desc"}
              </button>
            </div>
          </div>

          <p className="mb-2 text-[11px] text-[var(--muted)]">
            Showing {filtered.length} / {results.length}
          </p>

          <div
            ref={scrollRef}
            className="max-h-[min(70vh,640px)] overflow-auto"
            onScroll={(e) => setScrollTop(e.currentTarget.scrollTop)}
          >
            <div style={{ height: topPad }} />
            <ul className="space-y-2">
              {windowed.map(({ wafer, index }) => {
                const active = index === selectedIndex;
                const compared = comparisonIndices.includes(index);
                return (
                  <li key={`${wafer.wafer_id}-${index}`} style={{ minHeight: ROW_HEIGHT - 8 }}>
                    <div
                      className={cn(
                        "rounded-lg border px-3 py-2 transition",
                        active
                          ? "border-signal-info bg-signal-info/10"
                          : "border-[var(--line)] hover:border-ink-400",
                      )}
                    >
                      <div className="flex items-start gap-2">
                        <input
                          type="checkbox"
                          checked={compared}
                          onChange={() => toggleComparison(index)}
                          title="Add to comparison"
                          className="mt-1"
                        />
                        <button
                          type="button"
                          onClick={() => selectWafer(index)}
                          className="min-w-0 flex-1 text-left"
                        >
                          <p className="truncate font-mono text-xs">
                            {readWaferName(wafer)}
                          </p>
                          <p className="mt-0.5 text-sm font-medium">
                            {readDefectType(wafer)}
                          </p>
                          <div className="mt-1.5 flex flex-wrap gap-x-2 gap-y-0.5 text-[11px] text-[var(--muted)]">
                            <span>LOT {displayLot(wafer)}</span>
                            <span>
                              Yield {formatPercent(wafer.yield_summary?.yield_percent)}
                            </span>
                            <span>
                              Conf {formatPercent(wafer.classification?.confidence)}
                            </span>
                            <span className="font-semibold text-signal-good">
                              Analyzed
                            </span>
                          </div>
                        </button>
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
            <div style={{ height: bottomPad }} />
          </div>
        </>
      )}
    </aside>
  );
}
