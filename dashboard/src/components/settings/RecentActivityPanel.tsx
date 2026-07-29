"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ChevronLeft, ChevronRight, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuditLogs } from "@/hooks/useAuditLogs";
import { isLiveApi } from "@/lib/api/config";

const PAGE_SIZE = 10;

function formatAction(action: string): string {
  return action.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatTime(iso?: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function statusClass(status?: string | null, severity?: string): string {
  if (status === "failed" || severity === "error") return "text-red-400";
  if (status === "completed" || severity === "info") return "text-emerald-400";
  if (severity === "warning") return "text-amber-400";
  return "text-slate-300";
}

export function RecentActivityPanel() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [actionFilter, setActionFilter] = useState("");
  const params = useMemo(
    () => ({
      page,
      page_size: PAGE_SIZE,
      search: search.trim() || undefined,
      action: actionFilter || undefined,
    }),
    [page, search, actionFilter]
  );
  const { data, isLoading, isError } = useAuditLogs(params);
  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.1 }}
      className="settings-panel glass-card gradient-border hover-lift col-span-full mt-8 p-8"
    >
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">Recent Activity</h2>
          <p className="mt-1 text-sm text-slate-400">
            Audit trail for uploads, parser events, and account actions.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
            <Input
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              placeholder="Search activity…"
              className="w-56 border-[#2D3748] bg-[#090B12] pl-9"
            />
          </div>
          <Input
            value={actionFilter}
            onChange={(e) => {
              setActionFilter(e.target.value);
              setPage(1);
            }}
            placeholder="Filter by action"
            className="w-44 border-[#2D3748] bg-[#090B12]"
          />
        </div>
      </div>

      {!isLiveApi() && (
        <p className="text-sm text-slate-500">Audit history is available in live API mode only.</p>
      )}

      {isLiveApi() && (
        <div className="overflow-x-auto rounded-xl border border-[#2D3748]/60">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-[#111827]/80 text-slate-400">
              <tr>
                <th className="px-4 py-3 font-medium">Time</th>
                <th className="px-4 py-3 font-medium">Action</th>
                <th className="px-4 py-3 font-medium">User</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Details</th>
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                    Loading activity…
                  </td>
                </tr>
              )}
              {isError && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-red-400">
                    Unable to load audit history.
                  </td>
                </tr>
              )}
              {!isLoading && !isError && data?.items.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                    No audit events found.
                  </td>
                </tr>
              )}
              {data?.items.map((row) => (
                <tr key={row.id} className="border-t border-[#2D3748]/40 hover:bg-[#111827]/40">
                  <td className="whitespace-nowrap px-4 py-3 text-slate-300">
                    {formatTime(row.created_at)}
                  </td>
                  <td className="px-4 py-3 text-white">{formatAction(row.action)}</td>
                  <td className="px-4 py-3 text-slate-300">{row.username ?? "—"}</td>
                  <td className={`px-4 py-3 ${statusClass(row.status, row.severity)}`}>
                    {row.status ?? row.severity ?? "—"}
                  </td>
                  <td className="max-w-md truncate px-4 py-3 text-slate-400">
                    {row.message ?? row.filename ?? row.entity_id ?? "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {isLiveApi() && data && data.total > PAGE_SIZE && (
        <div className="mt-4 flex items-center justify-between text-sm text-slate-400">
          <span>
            Page {page} of {totalPages} · {data.total} events
          </span>
          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="border-[#2D3748]"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="border-[#2D3748]"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </motion.section>
  );
}
