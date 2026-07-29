"use client";

import { Area, AreaChart, ResponsiveContainer } from "recharts";
import { resolveKpiIcon } from "@/components/common/kpiIcons";
import { cn } from "@/lib/utils";
import type { KpiExecutiveSummaryCard, KpiWorkspaceLayoutPreset } from "@/types/kpiDrillDown";
import { WORKSPACE_LAYOUT_CLASS } from "@/types/kpiDrillDown";

const VARIANT_BORDER: Record<string, string> = {
  default: "border-[#2D3748]/60",
  success: "border-emerald-500/30",
  warning: "border-amber-500/30",
  danger: "border-red-500/30",
  info: "border-blue-500/30",
};

export function ExecutiveSummaryCard({ card }: { card: KpiExecutiveSummaryCard }) {
  const Icon = resolveKpiIcon(card.icon);
  const data = card.sparkline.map((v, i) => ({ i, v }));
  const gradId = `sum-spark-${card.id}`;

  return (
    <div
      className={cn(
        "rounded-xl border bg-gradient-to-br from-[#121826] to-[#0d111c] p-4 transition hover:border-[rgba(139,92,246,0.4)]",
        VARIANT_BORDER[card.variant ?? "default"]
      )}
    >
      <div className="mb-2 flex items-center justify-between">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[rgba(124,58,237,0.18)] text-[#8B5CF6]">
          <Icon className="h-4 w-4" />
        </div>
      </div>
      <p className="text-[11px] font-medium uppercase tracking-wider text-[#94A3B8]">{card.label}</p>
      <p className="mt-1 truncate text-xl font-bold tabular-nums text-white">{card.value}</p>
      <div className="mt-3 h-8 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <Area type="monotone" dataKey="v" stroke="#8B5CF6" strokeWidth={1.5} fill={`url(#${gradId})`} dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function WorkspaceSection({
  row,
  title,
  children,
  action,
}: {
  row: number;
  title: string;
  children: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <section aria-label={title}>
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-md bg-[#8B5CF6]/20 text-[11px] font-bold text-[#A78BFA]">
            {row}
          </span>
          <h3 className="text-sm font-bold uppercase tracking-wider text-white">{title}</h3>
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

export function FilterChip({ label, value }: { label: string; value: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-lg border border-[#2D3748]/80 bg-[#0A1020] px-2.5 py-1 text-[11px]">
      <span className="text-[#64748B]">{label}</span>
      <span className="font-semibold text-[#E2E8F0]">{value}</span>
    </span>
  );
}

export function MetaChip({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-[#2D3748]/50 bg-[#0A1020]/80 px-3 py-2">
      <p className="text-[10px] uppercase tracking-wider text-[#64748B]">{label}</p>
      <p className="mt-0.5 text-xs font-semibold text-white">{value}</p>
    </div>
  );
}

export function WorkspaceSkeleton({ layoutPreset = "standard" }: { layoutPreset?: KpiWorkspaceLayoutPreset }) {
  const cardCount = layoutPreset === "failure" ? 8 : layoutPreset === "diagnosis" ? 10 : layoutPreset === "optimization" ? 9 : 6;
  return (
    <div className={cn(WORKSPACE_LAYOUT_CLASS[layoutPreset], "animate-pulse")}>
      <div className="h-24 border-b border-[#2D3748]/60 bg-[#121826]/50" />
      <div className="flex-1 space-y-6 p-5">
        <div
          className={cn(
            "grid gap-3",
            layoutPreset === "diagnosis"
              ? "grid-cols-5 xl:grid-cols-10"
              : layoutPreset === "optimization"
                ? "grid-cols-3 xl:grid-cols-9"
              : layoutPreset === "failure"
                ? "grid-cols-4 xl:grid-cols-8"
                : "grid-cols-6"
          )}
        >
          {Array.from({ length: cardCount }).map((_, i) => (
            <div key={i} className="h-28 rounded-xl bg-[#1e293b]/40" />
          ))}
        </div>
        <div className="h-64 rounded-xl bg-[#1e293b]/40" />
        <div className="grid grid-cols-2 gap-3">
          <div className="h-56 rounded-xl bg-[#1e293b]/40" />
          <div className="h-56 rounded-xl bg-[#1e293b]/40" />
        </div>
      </div>
    </div>
  );
}
