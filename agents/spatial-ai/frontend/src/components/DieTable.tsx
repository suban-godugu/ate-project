"use client";

import { useMemo, useState } from "react";

import { useAnalysis } from "@/context/AnalysisContext";
import type { DieRecord } from "@/types/wafer";
import { cn } from "@/utils/format";

type SortKey = keyof Pick<DieRecord, "die_id" | "row" | "column" | "x" | "y" | "status">;

export function DieTable() {
  const { selected } = useAnalysis();
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("die_id");
  const [asc, setAsc] = useState(true);
  const [page, setPage] = useState(0);
  const pageSize = 12;

  const rows = useMemo(() => {
    const dies = selected?.dies ?? [];
    const filtered = dies.filter((die) => {
      const hay = `${die.die_id} ${die.row} ${die.column} ${die.x} ${die.y} ${die.status}`.toLowerCase();
      return hay.includes(query.toLowerCase());
    });
    filtered.sort((a, b) => {
      const left = a[sortKey];
      const right = b[sortKey];
      if (left === right) return 0;
      if (left > right) return asc ? 1 : -1;
      return asc ? -1 : 1;
    });
    return filtered;
  }, [selected, query, sortKey, asc]);

  const pageCount = Math.max(1, Math.ceil(rows.length / pageSize));
  const pageRows = rows.slice(page * pageSize, page * pageSize + pageSize);

  const onSort = (key: SortKey) => {
    if (sortKey === key) setAsc((value) => !value);
    else {
      setSortKey(key);
      setAsc(true);
    }
  };

  return (
    <section className="panel p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="panel-title">Die Table</h2>
        <input
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            setPage(0);
          }}
          placeholder="Search dies…"
          className="w-full max-w-xs rounded-lg border border-[var(--line)] bg-transparent px-3 py-2 text-sm outline-none focus:border-signal-info"
        />
      </div>

      {!selected ? (
        <p className="text-sm text-[var(--muted)]">No die list from backend yet.</p>
      ) : (
        <>
          <div className="overflow-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-wide text-[var(--muted)]">
                <tr>
                  {(
                    [
                      ["die_id", "Die ID"],
                      ["row", "Row"],
                      ["column", "Column"],
                      ["x", "X"],
                      ["y", "Y"],
                      ["status", "Status"],
                    ] as [SortKey, string][]
                  ).map(([key, label]) => (
                    <th key={key} className="cursor-pointer px-2 py-2" onClick={() => onSort(key)}>
                      {label}
                      {sortKey === key ? (asc ? " ↑" : " ↓") : ""}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {pageRows.map((die) => (
                  <tr key={die.die_id} className="border-t border-[var(--line)]">
                    <td className="px-2 py-2 font-mono">{die.die_id}</td>
                    <td className="px-2 py-2 font-mono">{die.row}</td>
                    <td className="px-2 py-2 font-mono">{die.column}</td>
                    <td className="px-2 py-2 font-mono">{die.x}</td>
                    <td className="px-2 py-2 font-mono">{die.y}</td>
                    <td className="px-2 py-2">
                      <span
                        className={cn(
                          "rounded-full px-2 py-0.5 text-xs font-semibold",
                          die.status === "FAIL"
                            ? "bg-signal-fail/15 text-signal-fail"
                            : "bg-signal-good/15 text-signal-good",
                        )}
                      >
                        {die.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-4 flex items-center justify-between text-xs text-[var(--muted)]">
            <span>
              {rows.length} dies · page {page + 1}/{pageCount}
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                className="rounded border border-[var(--line)] px-2 py-1 disabled:opacity-40"
                disabled={page <= 0}
                onClick={() => setPage((value) => Math.max(0, value - 1))}
              >
                Prev
              </button>
              <button
                type="button"
                className="rounded border border-[var(--line)] px-2 py-1 disabled:opacity-40"
                disabled={page >= pageCount - 1}
                onClick={() => setPage((value) => Math.min(pageCount - 1, value + 1))}
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </section>
  );
}
