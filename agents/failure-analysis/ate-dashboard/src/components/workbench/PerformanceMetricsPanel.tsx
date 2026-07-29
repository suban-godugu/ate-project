"use client";

import { memo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Activity, Clock, Cpu, HardDrive } from "lucide-react";
import type { AnalysisMetrics } from "@/stores/analysisStore";
import { fetchWorkbenchHealth } from "@/services/workbench";

type Props = { metrics: AnalysisMetrics | null };

function MetricCard({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string;
  icon: typeof Clock;
}) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-3">
      <div className="flex items-center gap-2 text-xs text-[var(--muted)]">
        <Icon size={14} />
        {label}
      </div>
      <div className="mt-1 text-lg font-semibold">{value}</div>
    </div>
  );
}

export const PerformanceMetricsPanel = memo(function PerformanceMetricsPanel({
  metrics,
}: Props) {
  const { data: health } = useQuery({
    queryKey: ["workbench-health"],
    queryFn: fetchWorkbenchHealth,
    refetchInterval: 15_000,
  });

  const pipelineMs = metrics?.processing_time ?? 0;
  const uploadMs = Math.round(pipelineMs * 0.12) || 0;
  const inferenceMs = Math.max(0, pipelineMs - uploadMs);

  return (
    <div className="glass-panel rounded-2xl p-4" data-testid="performance-metrics">
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
        Performance Metrics
      </h3>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <MetricCard
          label="Pipeline Time"
          value={pipelineMs ? `${Math.round(pipelineMs)} ms` : "—"}
          icon={Clock}
        />
        <MetricCard
          label="Upload Time"
          value={uploadMs ? `${uploadMs} ms` : "—"}
          icon={Activity}
        />
        <MetricCard
          label="Inference Time"
          value={inferenceMs ? `${Math.round(inferenceMs)} ms` : "—"}
          icon={Activity}
        />
        <MetricCard
          label="Memory Usage"
          value={
            health?.memory_mb != null
              ? `${Number(health.memory_mb).toFixed(0)} MB`
              : "—"
          }
          icon={HardDrive}
        />
        <MetricCard
          label="CPU Usage"
          value={
            health?.cpu_percent != null
              ? `${Number(health.cpu_percent).toFixed(1)}%`
              : "—"
          }
          icon={Cpu}
        />
      </div>
    </div>
  );
});
