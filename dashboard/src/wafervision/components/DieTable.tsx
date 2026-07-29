"use client";

import { useMemo, useState } from "react";
import { useAnalysis } from "@/wafervision/hooks/useAnalysis";
import { cn } from "@/wafervision/utils/format";

const PAGE_SIZE = 12;

type SortKey = "die_id" | "row" | "column" | "x" | "y" | "status";

export function DieTable() {
  const { selected } = useAnalysis();
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("die_id");
  const [sortAsc, setSortAsc] = useState(true);
  const [page, setPage] = useState(0);

  const rows = useMemo(() => {
    const dies = selected?.dies ?? [];
    const q = search.trim().toLowerCase();
    let list = dies.map((d) => ({
      die_id: d.die_id || d.id || "—",
      row: d.row ?? -1,
      column: d.column ?? -1,
      x: d.x ?? -1,
      y: d.y ?? -1,
      status: d.status || "PASS",
    }));
    if (q) {
      list = list.filter((d) =>
        `${d.die_id} ${d.row} ${d.column} ${d.x} ${d.y} ${d.status}`
          .toLowerCase()
          .includes(q)
      );
    }
    list.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      const cmp =
        typeof av === "number" && typeof bv === "number"
          ? av - bv
          : String(av).localeCompare(String(bv));
      return sortAsc ? cmp : -cmp;
    });
    return list;
  }, [selected, search, sortKey, sortAsc]);

  if (!selected) {
    return (
      <section className="panel p-5">
        <h2 className="panel-title mb-3">Die Table</h2>
        <p className="text-sm" style={{ color: "var(--muted)" }}>
          No die list from backend yet.
        </p>
      </section>
    );
  }

  const pageCount = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
  const current = Math.min(page, pageCount - 1);
  const slice = rows.slice(current * PAGE_SIZE, current * PAGE_SIZE + PAGE_SIZE);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setSortAsc((v) => !v);
    else {
      setSortKey(key);
      setSortAsc(true);
    }
  };

  const headers: { key: SortKey; label: string }[] = [
    { key: "die_id", label: "Die ID" },
    { key: "row", label: "Row" },
    { key: "column", label: "Column" },
    { key: "x", label: "X" },
    { key: "y", label: "Y" },
    { key: "status", label: "Status" },
  ];

  return (
    <section className="panel p-5 space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="panel-title">Die Table</h2>
        <input
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(0);
          }}
          placeholder="Search dies…"
          className="rounded-lg border px-3 py-1.5 text-xs bg-transparent min-w-[180px]"
          style={{ borderColor: "var(--line)" }}
        />
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-[11px] uppercase tracking-wide" style={{ color: "var(--muted)" }}>
              {headers.map((h) => (
                <th key={h.key} className="px-2 py-2 text-left">
                  <button type="button" onClick={() => toggleSort(h.key)} className="hover:underline">
                    {h.label}
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {slice.map((d) => (
              <tr key={d.die_id} className="border-t" style={{ borderColor: "var(--line)" }}>
                <td className="px-2 py-2 font-mono">{d.die_id}</td>
                <td className="px-2 py-2 font-mono">{d.row}</td>
                <td className="px-2 py-2 font-mono">{d.column}</td>
                <td className="px-2 py-2 font-mono">{d.x}</td>
                <td className="px-2 py-2 font-mono">{d.y}</td>
                <td className="px-2 py-2">
                  <span
                    className={cn(
                      "rounded-full px-2 py-0.5 text-xs font-medium",
                      d.status === "FAIL"
                        ? "bg-signal-fail/15 text-signal-fail"
                        : "bg-signal-good/15 text-signal-good"
                    )}
                  >
                    {d.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between text-xs" style={{ color: "var(--muted)" }}>
        <span>
          {rows.length} dies · page {current + 1}/{pageCount}
        </span>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={current <= 0}
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            className="rounded-lg border px-3 py-1 disabled:opacity-40"
            style={{ borderColor: "var(--line)" }}
          >
            Prev
          </button>
          <button
            type="button"
            disabled={current >= pageCount - 1}
            onClick={() => setPage((p) => Math.min(pageCount - 1, p + 1))}
            className="rounded-lg border px-3 py-1 disabled:opacity-40"
            style={{ borderColor: "var(--line)" }}
          >
            Next
          </button>
        </div>
      </div>
    </section>
  );
}
