"use client";

import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import type { CoverageTableColumn, CoverageTableRow } from "@/types/scanCoverage";

interface Props {
  columns: CoverageTableColumn[];
  rows: CoverageTableRow[];
}

const PAGE_SIZE = 10;

export function RawCoverageTable({ columns, rows }: Props) {
  const [tableSearch, setTableSearch] = useState("");
  const [tablePage, setTablePage] = useState(0);
  const [visibleCols, setVisibleCols] = useState<Set<string>>(
    () => new Set(columns.filter((c) => c.defaultVisible !== false).map((c) => c.key))
  );

  const filteredRows = useMemo(() => {
    const q = tableSearch.toLowerCase();
    if (!q) return rows;
    return rows.filter((r) => Object.values(r).some((v) => String(v).toLowerCase().includes(q)));
  }, [rows, tableSearch]);

  const activeColumns = columns.filter((c) => visibleCols.has(c.key));
  const pageRows = filteredRows.slice(tablePage * PAGE_SIZE, (tablePage + 1) * PAGE_SIZE);
  const totalPages = Math.max(1, Math.ceil(filteredRows.length / PAGE_SIZE));

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <Input
          placeholder="Search records..."
          value={tableSearch}
          onChange={(e) => {
            setTableSearch(e.target.value);
            setTablePage(0);
          }}
          className="h-8 w-52 border-[#2D3748] bg-[#0A1020] text-xs"
        />
        <div className="flex flex-wrap gap-1">
          {columns.map((col) => (
            <button
              key={col.key}
              type="button"
              suppressHydrationWarning
              onClick={() =>
                setVisibleCols((prev) => {
                  const next = new Set(prev);
                  if (next.has(col.key)) next.delete(col.key);
                  else next.add(col.key);
                  return next;
                })
              }
              className={cn(
                "rounded px-2 py-1 text-[10px]",
                visibleCols.has(col.key) ? "bg-[#8B5CF6]/25 text-[#C4B5FD]" : "bg-[#1e293b]/60 text-[#64748B]"
              )}
            >
              {col.label}
            </button>
          ))}
        </div>
      </div>
      <div className="overflow-x-auto rounded-xl border border-[#2D3748]/60">
        <table className="w-full min-w-[720px] text-left text-xs">
          <thead className="bg-[#0A1020] text-[10px] uppercase tracking-wider text-[#64748B]">
            <tr>
              {activeColumns.map((col) => (
                <th key={col.key} className="px-3 py-2.5">
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row) => (
              <tr key={row.entityId} className="border-t border-[#2D3748]/30 hover:bg-[#8B5CF6]/5">
                {activeColumns.map((col) => (
                  <td key={col.key} className="px-3 py-2 text-[#CBD5E1]">
                    {String(row[col.key as keyof CoverageTableRow] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-2 flex items-center justify-between text-xs text-[#64748B]">
        <span>{filteredRows.length} records</span>
        <div className="flex gap-2">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            disabled={tablePage === 0}
            onClick={() => setTablePage((p) => p - 1)}
          >
            Prev
          </Button>
          <span>
            {tablePage + 1} / {totalPages}
          </span>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            disabled={tablePage >= totalPages - 1}
            onClick={() => setTablePage((p) => p + 1)}
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  );
}
