"use client";

import { useMemo, useState } from "react";
import { ArrowDown, ArrowUp, Search } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import type { PatternRow, Recommendation } from "@/types/dashboard";

type SortKey = keyof PatternRow;
type SortDir = "asc" | "desc";

const PAGE_SIZE = 5;

const recStyles: Record<
  Recommendation,
  { variant: "default" | "secondary" | "destructive"; className?: string }
> = {
  Keep: { variant: "default", className: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30" },
  Review: { variant: "secondary", className: "bg-amber-500/15 text-amber-400 border-amber-500/30" },
  Remove: { variant: "destructive", className: "bg-red-500/15 text-red-400 border-red-500/30" },
};

interface PatternTableProps {
  data: PatternRow[];
}

export function PatternTable({ data }: PatternTableProps) {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const [sortKey, setSortKey] = useState<SortKey>("id");
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    let rows = data.filter((r) => r.id.toLowerCase().includes(q));
    rows = [...rows].sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (typeof av === "number" && typeof bv === "number") {
        return sortDir === "asc" ? av - bv : bv - av;
      }
      return sortDir === "asc"
        ? String(av).localeCompare(String(bv))
        : String(bv).localeCompare(String(av));
    });
    return rows;
  }, [data, search, sortKey, sortDir]);

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const pageData = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  const SortIcon = ({ col }: { col: SortKey }) =>
    sortKey === col ? (
      sortDir === "asc" ? (
        <ArrowUp className="ml-1 inline h-3 w-3" />
      ) : (
        <ArrowDown className="ml-1 inline h-3 w-3" />
      )
    ) : null;

  return (
    <div id="patterns" className="glass-card gradient-border overflow-hidden p-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-white">Pattern Analysis</h3>
          <p className="text-sm text-slate-400">
            Enterprise test pattern performance and recommendations
          </p>
        </div>
        <div className="relative w-full max-w-xs">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <Input
            placeholder="Search patterns..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(0);
            }}
            className="h-9 border-[#2D3748] bg-[#0A1020] pl-9 text-sm"
          />
        </div>
      </div>

      <div className="overflow-x-auto rounded-xl border border-[#2D3748]/60">
        <Table>
          <TableHeader>
            <TableRow className="border-[#2D3748] hover:bg-transparent">
              {(
                [
                  ["id", "Pattern ID"],
                  ["testTime", "Test Time"],
                  ["cost", "Cost"],
                  ["failRate", "Fail Rate"],
                  ["detectPower", "Detect Power"],
                  ["roiScore", "ROI Score"],
                  ["recommendation", "Recommendation"],
                ] as [SortKey, string][]
              ).map(([key, label]) => (
                <TableHead
                  key={key}
                  className="sticky top-0 cursor-pointer bg-[#111827] text-slate-400 hover:text-white"
                  onClick={() => toggleSort(key)}
                >
                  {label}
                  <SortIcon col={key} />
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {pageData.map((row) => {
              const rec = recStyles[row.recommendation];
              return (
                <TableRow
                  key={row.id}
                  className="border-[#2D3748]/60 transition-colors hover:bg-[#7C3AED]/5"
                >
                  <TableCell className="font-mono text-xs font-medium text-white">
                    {row.id}
                  </TableCell>
                  <TableCell>{row.testTime}s</TableCell>
                  <TableCell>${row.cost}</TableCell>
                  <TableCell>{row.failRate}%</TableCell>
                  <TableCell>{row.detectPower}%</TableCell>
                  <TableCell>{row.roiScore}</TableCell>
                  <TableCell>
                    <Badge
                      variant={rec.variant}
                      className={cn("border", rec.className)}
                    >
                      {row.recommendation}
                    </Badge>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>

      <div className="mt-4 flex items-center justify-between text-sm text-slate-400">
        <span>
          Showing {page * PAGE_SIZE + 1}–
          {Math.min((page + 1) * PAGE_SIZE, filtered.length)} of {filtered.length}
        </span>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            className="border-[#2D3748]"
            disabled={page === 0}
            onClick={() => setPage((p) => p - 1)}
          >
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="border-[#2D3748]"
            disabled={page >= totalPages - 1}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  );
}
