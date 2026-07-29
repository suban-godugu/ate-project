"use client";

import { Inbox, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EnterpriseKPISkeleton } from "@/components/common/EnterpriseKPICard";

interface EmptyStateProps {
  title?: string;
  message?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function EmptyState({
  title = "No data available",
  message = "Try adjusting your filters or upload new test data.",
  actionLabel = "Reset Filters",
  onAction,
}: EmptyStateProps) {
  return (
    <div className="glass-card flex flex-col items-center justify-center px-6 py-16 text-center">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-[#7C3AED]/10 text-[#7C3AED]">
        <Inbox className="h-8 w-8" aria-hidden="true" />
      </div>
      <h3 className="text-lg font-semibold text-white">{title}</h3>
      <p className="mt-2 max-w-md text-sm text-slate-400">{message}</p>
      {onAction && (
        <Button onClick={onAction} className="mt-6 rounded-xl bg-[#7C3AED] hover:bg-[#6D28D9]">
          {actionLabel}
        </Button>
      )}
    </div>
  );
}

interface ErrorCardProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorCard({ title = "Something went wrong", message, onRetry }: ErrorCardProps) {
  return (
    <div className="glass-card border border-red-500/30 p-4" role="alert">
      <p className="text-sm font-semibold text-red-400">{title}</p>
      <p className="mt-1 text-xs text-slate-400">{message}</p>
      {onRetry && (
        <Button
          variant="outline"
          size="sm"
          onClick={onRetry}
          className="mt-3 rounded-xl border-[#2D3748] text-xs"
        >
          <RefreshCw className="mr-1.5 h-3 w-3" />
          Retry
        </Button>
      )}
    </div>
  );
}

export function SkeletonBlock({ className = "h-32" }: { className?: string }) {
  return <div className={`animate-pulse rounded-xl bg-[#1e293b]/80 ${className}`} aria-hidden="true" />;
}

export function PageSkeleton() {
  return (
    <div className="dashboard-content" aria-busy="true" aria-label="Loading page">
      <div className="kpi-grid">
        {Array.from({ length: 6 }).map((_, i) => (
          <EnterpriseKPISkeleton key={i} />
        ))}
      </div>
      <SkeletonBlock className="h-72" />
      <div className="grid gap-6 lg:grid-cols-2">
        <SkeletonBlock className="h-64" />
        <SkeletonBlock className="h-64" />
      </div>
    </div>
  );
}

export function TableSkeleton() {
  return (
    <div className="space-y-3" aria-busy="true">
      <SkeletonBlock className="h-10" />
      {Array.from({ length: 5 }).map((_, i) => (
        <SkeletonBlock key={i} className="h-12" />
      ))}
    </div>
  );
}

export function ChartSkeleton() {
  return <SkeletonBlock className="h-64 w-full" aria-busy="true" />;
}
