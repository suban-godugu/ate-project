"use client";

import { LOT_TAXONOMY } from "@/wafervision/utils/lotTaxonomy";
import type { SortKey } from "@/wafervision/types";
import { useAnalysis } from "@/wafervision/hooks/useAnalysis";
import { filterAndSortWafers } from "@/wafervision/utils/batchAggregates";

const DEFECTS = [
  "All",
  "Center",
  "Donut",
  "Edge-Loc",
  "Edge-Ring",
  "Local",
  "Near-Full",
  "Normal",
  "Random",
  "Scratch",
];
const LOTS = ["All", ...LOT_TAXONOMY.map((t) => t.lot)];

const SORT_OPTIONS: { value: SortKey; label: string }[] = [
  { value: "name", label: "Name" },
  { value: "yield", label: "Yield" },
  { value: "confidence", label: "Confidence" },
  { value: "lot", label: "LOT" },
  { value: "defect", label: "Defect" },
  { value: "failDies", label: "Fail Dies" },
  { value: "goodDies", label: "Good Dies" },
];

const inputClass =
  "rounded-lg border border-[#2D3748] bg-transparent px-2 py-1.5 text-xs text-slate-100 focus:border-[#7C3AED] focus:outline-none";

export function WaferFilterToolbar() {
  const { results, filters, setFilters } = useAnalysis();
  if (!results.length) return null;

  const filtered = filterAndSortWafers(results, filters);

  return (
    <section className="panel space-y-2 p-4">
      <div className="flex flex-wrap items-end gap-2">
        <input
          type="search"
          value={filters.search}
          onChange={(e) => setFilters({ search: e.target.value })}
          placeholder="Search name · defect · LOT · yield."
          className={`${inputClass} min-w-[180px] flex-1`}
        />
        <select
          value={filters.defectFilter}
          onChange={(e) => setFilters({ defectFilter: e.target.value })}
          className={inputClass}
          aria-label="Defect filter"
        >
          {DEFECTS.map((d) => (
            <option key={d} value={d}>
              {d === "All" ? "All Defects" : d}
            </option>
          ))}
        </select>
        <select
          value={filters.lotFilter}
          onChange={(e) => setFilters({ lotFilter: e.target.value })}
          className={inputClass}
          aria-label="LOT filter"
        >
          {LOTS.map((l) => (
            <option key={l} value={l}>
              {l === "All" ? "All LOTs" : l}
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
          className={`${inputClass} w-24`}
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
          className={`${inputClass} w-24`}
        />
        <input
          type="number"
          placeholder="Conf min."
          value={filters.confidenceMin ?? ""}
          onChange={(e) =>
            setFilters({
              confidenceMin: e.target.value === "" ? null : Number(e.target.value),
            })
          }
          className={`${inputClass} w-24`}
        />
        <select
          value={filters.sortKey}
          onChange={(e) => setFilters({ sortKey: e.target.value as SortKey })}
          className={inputClass}
          aria-label="Sort key"
        >
          {SORT_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={() => setFilters({ sortAsc: !filters.sortAsc })}
          className="rounded-lg border border-[#2D3748] px-3 py-1.5 text-xs text-slate-200 hover:border-[#7C3AED]/50"
        >
          {filters.sortAsc ? "Asc" : "Desc"}
        </button>
      </div>
      <p className="text-xs text-[var(--muted)]">
        Showing {filtered.length} / {results.length}
      </p>
    </section>
  );
}
