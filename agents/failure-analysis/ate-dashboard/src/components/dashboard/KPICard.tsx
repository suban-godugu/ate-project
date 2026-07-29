"use client";

import { memo, type ReactNode } from "react";
import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export type KPICardProps = {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: { direction: "up" | "down" | "flat"; label: string };
  status?: "ok" | "warn" | "critical" | "neutral";
  icon?: LucideIcon;
  loading?: boolean;
  testId?: string;
};

function ShimmerBlock({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-lg bg-gradient-to-r from-white/5 via-white/10 to-white/5 bg-[length:200%_100%]",
        className,
      )}
      style={{ animation: "shimmer 1.6s ease-in-out infinite" }}
    />
  );
}

export const KPICard = memo(function KPICard({
  title,
  value,
  subtitle,
  trend,
  status = "neutral",
  icon: Icon,
  loading,
  testId,
}: KPICardProps) {
  const statusRing =
    status === "critical"
      ? "border-[var(--danger)]/30"
      : status === "warn"
        ? "border-[var(--warning)]/30"
        : status === "ok"
          ? "border-[var(--success)]/30"
          : "border-white/10";

  if (loading) {
    return (
      <div className={cn("glass-panel rounded-2xl border p-4", statusRing)} data-testid={testId}>
        <ShimmerBlock className="mb-3 h-3 w-24" />
        <ShimmerBlock className="mb-2 h-8 w-20" />
        <ShimmerBlock className="h-3 w-32" />
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("glass-panel rounded-2xl border p-4", statusRing)}
      data-testid={testId}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="text-xs uppercase tracking-wide text-[var(--muted)]">{title}</div>
        {Icon && (
          <div className="rounded-lg bg-[var(--accent-soft)] p-1.5 text-[var(--accent)]">
            <Icon size={14} />
          </div>
        )}
      </div>
      <div className="mt-2 text-2xl font-semibold tabular-nums">{value}</div>
      {(subtitle || trend) && (
        <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-[var(--muted)]">
          {subtitle && <span>{subtitle}</span>}
          {trend && (
            <span
              className={
                trend.direction === "up"
                  ? "text-[var(--danger)]"
                  : trend.direction === "down"
                    ? "text-[var(--success)]"
                    : ""
              }
            >
              {trend.label}
            </span>
          )}
        </div>
      )}
    </motion.div>
  );
});

export function KPIGridSkeleton({ count = 12 }: { count?: number }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
      {Array.from({ length: count }).map((_, i) => (
        <KPICard key={i} title="" value="" loading />
      ))}
    </div>
  );
}

export function DashboardEmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div
      className="glass-panel flex flex-col items-center justify-center rounded-2xl border border-dashed border-white/15 p-10 text-center"
      data-testid="dashboard-empty"
    >
      <h3 className="text-base font-semibold">{title}</h3>
      <p className="mt-2 max-w-md text-sm text-[var(--muted)]">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
