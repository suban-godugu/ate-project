"use client";

import { useMemo } from "react";

import { useAnalysis } from "@/hooks/useAnalysis";
import {
  filterAndSortWafers,
  type WaferSortKey,
} from "@/utils/batchAggregates";
import { DEFECT_CLASSES, LOT_TAXONOMY } from "@/utils/lotTaxonomy";

/**
 * Horizontal filter toolbar (formerly Wafer Sidebar filter controls).
 * Behaviour unchanged — same filter state and options.
 */
export function WaferFilterToolbar() {
  const { results, filters, setFilters } = useAnalysis();

  const filteredCount = useMemo(
    () => filterAndSortWafers(results, filters).length,
    [results, filters],
  );

  if (results.length === 0) {
    return null;
  }

  const fieldClass =
    "rounded-lg border border-[var(--line)] bg-transparent px-2 py-1.5 text-xs outline-none focus:border-signal-info";

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <input
          type="search"
          placeholder="Search name · defect · LOT · yield"
          value={filters.search}
          onChange={(e) => setFilters({ search: e.target.value })}
          className={`${fieldClass} min-w-[180px] flex-1`}
        />

        <select
          value={filters.defectFilter}
          onChange={(e) => setFilters({ defectFilter: e.target.value })}
          className={fieldClass}
          aria-label="Defect filter"
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
          className={fieldClass}
          aria-label="LOT filter"
        >
          <option value="All">All LOTs</option>
          {LOT_TAXONOMY.map(({ lot }) => (
            <option key={lot} value={lot}>
              {lot}
            </option>
          ))}
        </select>

        <input
          type="number"
          placeholder="Yield min"
          value={filters.yieldMin ?? ""}
          onChange={(e) =>
            setFilters({
              yieldMin: e.target.value === "" ? null : Number(e.target.value),
            })
          }
          className={`${fieldClass} w-[88px]`}
          aria-label="Yield min"
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
          className={`${fieldClass} w-[88px]`}
          aria-label="Yield max"
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
          className={`${fieldClass} w-[88px]`}
          aria-label="Confidence min"
        />

        <select
          value={filters.sortKey}
          onChange={(e) =>
            setFilters({ sortKey: e.target.value as WaferSortKey })
          }
          className={fieldClass}
          aria-label="Sort"
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
      <p className="text-[11px] text-[var(--muted)]">
        Showing {filteredCount} / {results.length}
      </p>
    </div>
  );
}
