"use client";

import type { LucideIcon } from "lucide-react";
import { AlertTriangle, Inbox, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PageSkeleton } from "@/components/platform/EmptyState";

export function EnterpriseLoadingState() {
  return <PageSkeleton />;
}

interface EnterpriseEmptyStateProps {
  title: string;
  description?: string;
  icon?: LucideIcon;
  actionLabel?: string;
  onAction?: () => void;
}

export function EnterpriseEmptyState({
  title,
  description = "Try adjusting your filters or upload new test data.",
  icon: Icon = Inbox,
  actionLabel,
  onAction,
}: EnterpriseEmptyStateProps) {
  return (
    <div className="glass-card flex flex-col items-center justify-center px-6 py-16 text-center">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-[#7C3AED]/10 text-[#7C3AED]">
        <Icon className="h-8 w-8" aria-hidden="true" />
      </div>
      <h3 className="text-lg font-semibold text-white">{title}</h3>
      <p className="mt-2 max-w-md text-sm text-slate-400">{description}</p>
      {onAction && actionLabel && (
        <Button onClick={onAction} className="mt-6 rounded-xl bg-[#7C3AED] hover:bg-[#6D28D9]">
          {actionLabel}
        </Button>
      )}
    </div>
  );
}

interface EnterpriseErrorStateProps {
  title?: string;
  description?: string;
  technicalDetails?: string;
  onRetry?: () => void;
}

export function EnterpriseErrorState({
  title = "Unable to load data",
  description = "The dashboard API returned an error. Your session may have expired or the backend may be unavailable.",
  technicalDetails,
  onRetry,
}: EnterpriseErrorStateProps) {
  return (
    <div className="glass-card flex flex-col items-center justify-center border border-red-500/30 px-6 py-16 text-center">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-red-500/10 text-red-400">
        <AlertTriangle className="h-8 w-8" aria-hidden="true" />
      </div>
      <h3 className="text-lg font-semibold text-white">{title}</h3>
      <p className="mt-2 max-w-md text-sm text-slate-400">{description}</p>
      {technicalDetails && (
        <p className="mt-3 max-w-lg truncate text-xs text-slate-500" title={technicalDetails}>
          {technicalDetails}
        </p>
      )}
      {onRetry && (
        <Button
          variant="outline"
          onClick={onRetry}
          className="mt-6 rounded-xl border-[#2D3748] text-sm"
        >
          <RefreshCw className="mr-2 h-4 w-4" />
          Retry
        </Button>
      )}
    </div>
  );
}
