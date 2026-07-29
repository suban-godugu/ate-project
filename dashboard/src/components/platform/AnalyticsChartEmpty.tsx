"use client";

import type { ReactNode } from "react";
import { isLiveApi } from "@/lib/api/config";

interface BlockedMeta {
  status?: string;
  reason?: string;
  blockedBy?: string;
}

interface AnalyticsChartEmptyProps {
  data: unknown[] | undefined;
  meta?: BlockedMeta;
  children: ReactNode;
  emptyLabel?: string;
}

export function AnalyticsChartEmpty({
  data,
  meta,
  children,
  emptyLabel = "No data available for current filters",
}: AnalyticsChartEmptyProps) {
  if (meta?.status === "blocked" && isLiveApi()) {
    return (
      <div className="flex min-h-[200px] flex-col items-center justify-center rounded-xl border border-dashed border-[#2D3748] bg-[#0A1020]/40 px-4 py-8 text-center">
        <p className="text-sm font-medium text-slate-300">Data not yet available</p>
        <p className="mt-1 max-w-sm text-xs text-slate-500">{meta.reason}</p>
        {meta.blockedBy ? (
          <p className="mt-2 font-mono text-[10px] text-slate-600">Requires: {meta.blockedBy}</p>
        ) : null}
      </div>
    );
  }
  if (isLiveApi() && (!data || (Array.isArray(data) && data.length === 0))) {
    return (
      <div className="flex min-h-[200px] items-center justify-center rounded-xl border border-dashed border-[#2D3748] bg-[#0A1020]/40 px-4 text-center text-sm text-slate-500">
        {emptyLabel}
      </div>
    );
  }
  return <>{children}</>;
}

export function chartMeta(
  charts: Record<string, unknown> | undefined,
  key: string
): BlockedMeta | undefined {
  const meta = charts?._meta as Record<string, BlockedMeta> | undefined;
  return meta?.[key];
}
