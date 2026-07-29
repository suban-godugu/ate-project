"use client";

import { memo, useMemo } from "react";
import Link from "next/link";
import {
  Activity,
  AlertTriangle,
  Brain,
  FileStack,
  GitFork,
  Layers,
  Percent,
  Repeat2,
  ScanSearch,
  Target,
  FileText,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useDashboard } from "@/hooks/useDashboard";
import { useEmbedMode } from "@/hooks/useEmbedMode";
import type { AnalysisMetrics } from "@/stores/analysisStore";
import {
  DashboardEmptyState,
  KPICard,
  KPIGridSkeleton,
} from "@/components/dashboard/KPICard";

type KPIDef = {
  label: string;
  key: keyof AnalysisMetrics;
  format?: "number" | "percent" | "ms";
  icon: LucideIcon;
  subtitle?: (m: AnalysisMetrics) => string | undefined;
  status?: (m: AnalysisMetrics) => "ok" | "warn" | "critical" | "neutral";
};

const KPI_DEFS: KPIDef[] = [
  {
    label: "Imported Test Files",
    key: "imported_test_files",
    icon: FileStack,
    subtitle: (m) =>
      `${m.total_tests.toLocaleString()} records · ${m.total_passed} pass · ${m.total_failed} fail`,
  },
  {
    label: "Overall Failure Rate",
    key: "overall_failure_rate",
    format: "percent",
    icon: Percent,
    subtitle: (m) => `Yield ${Number((m as AnalysisMetrics & { yield_pct?: number }).yield_pct ?? 0).toFixed(1)}%`,
    status: (m) => (m.overall_failure_rate > 15 ? "critical" : m.overall_failure_rate > 5 ? "warn" : "ok"),
  },
  {
    label: "AI Detection Accuracy",
    key: "ai_detection_accuracy",
    format: "percent",
    icon: Brain,
    status: (m) => (m.ai_detection_accuracy >= 95 ? "ok" : m.ai_detection_accuracy >= 80 ? "warn" : "critical"),
  },
  {
    label: "Failing Test Patterns",
    key: "failing_test_patterns",
    icon: ScanSearch,
    subtitle: (m) => `${m.recurring_failures} clustered signatures`,
  },
  {
    label: "Die Failure Rate",
    key: "die_failure_rate",
    format: "percent",
    icon: Target,
  },
  {
    label: "Wafer Failure Rate",
    key: "wafer_failure_rate",
    format: "percent",
    icon: Layers,
  },
  {
    label: "Lot Failure Rate",
    key: "lot_failure_rate",
    format: "percent",
    icon: Activity,
  },
  {
    label: "Fault Categories",
    key: "fault_categories",
    icon: AlertTriangle,
    subtitle: () => "Bins + testers + wafers",
  },
  {
    label: "Root Cause Confidence",
    key: "root_cause_confidence",
    format: "percent",
    icon: Brain,
  },
  {
    label: "Recurring Failures",
    key: "recurring_failures",
    icon: Repeat2,
  },
  {
    label: "Failure Correlations",
    key: "failure_correlations",
    icon: GitFork,
  },
  {
    label: "Failure Reports",
    key: "failure_reports",
    icon: FileText,
    subtitle: (m) =>
      m.processing_time ? `Processed in ${(m.processing_time / 1000).toFixed(1)}s` : undefined,
  },
];

function formatValue(value: number, format?: KPIDef["format"]) {
  if (format === "percent") return `${Number(value || 0).toFixed(2)}%`;
  if (format === "ms") return `${Number(value || 0).toFixed(0)} ms`;
  return Number(value || 0).toLocaleString();
}

export const AnalysisKPICards = memo(function AnalysisKPICards() {
  const embed = useEmbedMode();
  const {
    metrics,
    executionId,
    datasetId,
    isLoading,
    isEmpty,
    isAnalysisRunning,
    isError,
    error,
  } = useDashboard();

  const cards = useMemo(() => {
    if (!metrics) return null;
    return KPI_DEFS.map((def) => ({
      ...def,
      value: formatValue(metrics[def.key], def.format),
      subtitleText: def.subtitle?.(metrics),
      cardStatus: def.status?.(metrics) ?? "neutral",
    }));
  }, [metrics]);

  if (isError && !metrics) {
    return (
      <DashboardEmptyState
        title="Backend unavailable"
        description={error?.message || "Could not load analysis metrics from the API."}
        action={
          embed ? undefined : (
            <Link href="/upload" className="text-sm text-[var(--accent)] hover:underline">
              Retry from Upload
            </Link>
          )
        }
      />
    );
  }

  if (isEmpty && !isAnalysisRunning) {
    return (
      <DashboardEmptyState
        title="No analysis dataset"
        description={
          embed
            ? "Upload STIL and tester logs from the VERILUMEN top bar, then wait for Failure analysis to finish."
            : "Upload STIL and tester logs, then run Analyze to populate live KPI cards from the backend."
        }
        action={
          embed ? undefined : (
            <Link
              href="/upload"
              className="inline-flex rounded-xl bg-[var(--accent)] px-4 py-2 text-sm font-medium text-white"
            >
              Open Upload
            </Link>
          )
        }
      />
    );
  }

  if (isAnalysisRunning || (isLoading && !metrics)) {
    return <KPIGridSkeleton count={12} />;
  }

  if (!metrics || !cards) {
    return (
      <DashboardEmptyState
        title="No metrics available"
        description="Analysis did not return KPI metrics. Check pipeline status or re-run Analyze."
      />
    );
  }

  return (
    <div className="space-y-3">
      {(executionId || datasetId) && (
        <p className="font-mono text-xs text-[var(--muted)]">
          {datasetId ? `dataset=${datasetId}` : ""}
          {executionId ? ` · execution=${executionId}` : ""}
        </p>
      )}
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
        {cards.map((card) => (
          <KPICard
            key={card.key}
            title={card.label}
            value={card.value}
            subtitle={card.subtitleText}
            status={card.cardStatus}
            icon={card.icon}
            testId={`kpi-${card.key}`}
          />
        ))}
      </div>
    </div>
  );
});
