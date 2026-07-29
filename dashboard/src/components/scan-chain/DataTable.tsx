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

type SortDir = "asc" | "desc";

interface Column<T> {
  key: keyof T | string;
  label: string;
  render?: (row: T) => React.ReactNode;
  sortable?: boolean;
}

interface DataTableProps<T extends object> {
  title: string;
  subtitle?: string;
  data: T[];
  columns: Column<T>[];
  searchKeys?: (keyof T)[];
  searchPlaceholder?: string;
  pageSize?: number;
  rowKey: keyof T;
  action?: React.ReactNode;
}

export function DataTable<T extends object>({
  title,
  subtitle,
  data,
  columns,
  searchKeys,
  searchPlaceholder = "Search...",
  pageSize = 5,
  rowKey,
  action,
}: DataTableProps<T>) {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const [sortKey, setSortKey] = useState<keyof T>(
    (columns[0]?.key as keyof T) ?? ("" as keyof T)
  );
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    let rows = data;
    if (q && searchKeys) {
      rows = data.filter((row) =>
        searchKeys.some((key) => String(row[key]).toLowerCase().includes(q))
      );
    }
    return [...rows].sort((a, b) => {
      const av = a[sortKey as keyof T];
      const bv = b[sortKey as keyof T];
      if (typeof av === "number" && typeof bv === "number") {
        return sortDir === "asc" ? av - bv : bv - av;
      }
      return sortDir === "asc"
        ? String(av).localeCompare(String(bv))
        : String(bv).localeCompare(String(av));
    });
  }, [data, search, searchKeys, sortKey, sortDir]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const pageData = filtered.slice(page * pageSize, (page + 1) * pageSize);

  const toggleSort = (key: keyof T) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  const SortIcon = ({ col }: { col: keyof T | string }) =>
    sortKey === col ? (
      sortDir === "asc" ? (
        <ArrowUp className="ml-1 inline h-3 w-3" />
      ) : (
        <ArrowDown className="ml-1 inline h-3 w-3" />
      )
    ) : null;

  return (
    <div className="glass-card gradient-border overflow-hidden p-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-white">{title}</h3>
          {subtitle && <p className="text-sm text-slate-400">{subtitle}</p>}
        </div>
        <div className="flex items-center gap-3">
          {searchKeys && (
            <div className="relative w-full max-w-xs">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
              <Input
                placeholder={searchPlaceholder}
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(0);
                }}
                className="h-9 border-[#2D3748] bg-[#0A1020] pl-9 text-sm"
                suppressHydrationWarning
              />
            </div>
          )}
          {action}
        </div>
      </div>

      <div className="overflow-x-auto rounded-xl border border-[#2D3748]/60">
        <Table>
          <TableHeader>
            <TableRow className="border-[#2D3748] hover:bg-transparent">
              {columns.map((col) => (
                <TableHead
                  key={String(col.key)}
                  className={`sticky top-0 bg-[#111827] text-slate-400 ${
                    col.sortable !== false ? "cursor-pointer hover:text-white" : ""
                  }`}
                  onClick={() => col.sortable !== false && col.key in (data[0] ?? {}) && toggleSort(col.key as keyof T)}
                >
                  {col.label}
                  {col.sortable !== false && <SortIcon col={col.key} />}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {pageData.map((row) => (
              <TableRow
                key={String(row[rowKey])}
                className="border-[#2D3748]/60 transition-colors hover:bg-[#7C3AED]/5"
              >
                {columns.map((col) => (
                  <TableCell key={String(col.key)}>
                    {col.render
                      ? col.render(row)
                      : col.key in row
                        ? String(row[col.key as keyof T] ?? "")
                        : ""}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <div className="mt-4 flex items-center justify-between text-sm text-slate-400">
        <span>
          Showing {filtered.length === 0 ? 0 : page * pageSize + 1}–
          {Math.min((page + 1) * pageSize, filtered.length)} of {filtered.length}
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

export function StatusBadge({
  status,
  variant,
}: {
  status: string;
  variant?: "success" | "warning" | "danger" | "info" | "neutral";
}) {
  const styles = {
    success: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
    warning: "bg-amber-500/15 text-amber-400 border-amber-500/30",
    danger: "bg-red-500/15 text-red-400 border-red-500/30",
    info: "bg-cyan-500/15 text-cyan-400 border-cyan-500/30",
    neutral: "bg-slate-500/15 text-slate-400 border-slate-500/30",
  };
  return (
    <Badge variant="outline" className={`border ${styles[variant ?? "neutral"]}`}>
      {status}
    </Badge>
  );
}

export function PriorityBadge({ priority }: { priority: string }) {
  const variant =
    priority === "High" || priority === "Critical"
      ? "danger"
      : priority === "Medium" || priority === "Warning"
        ? "warning"
        : "success";
  return <StatusBadge status={priority} variant={variant} />;
}
