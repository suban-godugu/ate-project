"use client";

import { ArrowDown, CheckCircle2, FileText, Play, UserPlus, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MetaChip } from "@/components/common/kpi-drilldown/KpiWorkspaceSections";
import { cn } from "@/lib/utils";
import type {
  KpiAiDecisionOverview,
  KpiAiExplanation,
  KpiApprovalAction,
  KpiExpectedImpactCard,
  KpiImpactMetric,
} from "@/types/kpiDrillDown";

export function KpiAiDecisionPanel({
  data,
  variant = "pattern",
}: {
  data: KpiAiDecisionOverview;
  variant?: "pattern" | "testOptimization" | "scanDebug";
}) {
  const categoryLabel =
    variant === "testOptimization"
      ? "Optimization Category"
      : variant === "scanDebug"
        ? "Recommendation Category"
        : "Recommendation Category";
  const reasonLabel =
    variant === "testOptimization" ? "Recommendation Reason" : variant === "scanDebug" ? undefined : undefined;
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <div className="rounded-xl border border-[rgba(139,92,246,0.3)] bg-gradient-to-br from-[#121826] to-[#0d111c] p-4 lg:col-span-2">
        <p className="text-[10px] font-bold uppercase tracking-wider text-[#64748B]">{categoryLabel}</p>
        <p className="mt-1 text-lg font-bold text-white">{data.category}</p>
        {reasonLabel && <p className="mt-2 text-[10px] font-bold uppercase tracking-wider text-[#64748B]">{reasonLabel}</p>}
        <p className="mt-3 text-sm text-[#CBD5E1]">{data.reason}</p>
        <p className="mt-2 text-xs text-[#94A3B8]">Goal: {data.optimizationGoal}</p>
      </div>
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-1">
        {[
          { label: "Historical Success", value: data.historicalSuccessRate },
          { label: "Similar Cases", value: String(data.similarCases) },
          { label: "Confidence", value: `${data.confidence}%` },
          { label: "Difficulty", value: data.implementationDifficulty },
          { label: "Risk", value: data.riskLevel },
        ].map((item) => (
          <MetaChip key={item.label} label={item.label} value={item.value} />
        ))}
      </div>
      <div className="grid gap-2 sm:grid-cols-2 lg:col-span-3 lg:grid-cols-2">
        <MetaChip label="Engineering Benefit" value={data.engineeringBenefit} />
        <MetaChip label="Business Benefit" value={data.businessBenefit} />
      </div>
    </div>
  );
}

export function KpiAiExplanationPanel({ data }: { data: KpiAiExplanation }) {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <div className="rounded-xl border border-[rgba(139,92,246,0.25)] bg-[#121826]/80 p-4 lg:col-span-2">
        <p className="text-sm font-semibold text-white">{data.recommendationReason}</p>
        <div className="mt-4 space-y-2">
          {data.featureImportance.map((f) => (
            <div key={f.feature}>
              <div className="mb-1 flex justify-between text-[11px]">
                <span className="text-[#94A3B8]">{f.feature}</span>
                <span className="text-[#C4B5FD]">{f.weight}%</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-[#1e293b]">
                <div className="h-full rounded-full bg-[#8B5CF6]" style={{ width: `${f.weight}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="space-y-2">
        <MetaChip label="Alternative" value={data.alternative} />
        <MetaChip label="Risk Analysis" value={data.riskAnalysis} />
        <MetaChip label="Expected Outcome" value={data.expectedOutcome} />
        <MetaChip label="Confidence" value={`${data.confidence}%`} />
        <div className="rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/60 p-3">
          <p className="mb-2 text-[10px] font-bold uppercase tracking-wider text-[#64748B]">Similar Cases</p>
          <div className="flex flex-wrap gap-1">
            {data.similarCases.map((c) => (
              <span key={c} className="rounded-md bg-[#1e293b] px-2 py-0.5 text-xs text-[#CBD5E1]">
                {c}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export function KpiExpectedImpactPanel({ metrics }: { metrics: KpiExpectedImpactCard[] }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
      {metrics.map((m) => (
        <div
          key={m.label}
          className={cn(
            "rounded-xl border bg-[#121826]/80 p-4",
            m.variant === "success" ? "border-emerald-500/30" : "border-[rgba(139,92,246,0.2)]"
          )}
        >
          <p className="text-[11px] uppercase tracking-wider text-[#64748B]">{m.label}</p>
          <p className="mt-1 text-xl font-bold text-white">{m.value}</p>
          <p className="mt-1 text-xs text-emerald-400">{m.delta}</p>
        </div>
      ))}
    </div>
  );
}

export function KpiSimulationPanel({
  metrics,
  hero = false,
}: {
  metrics: KpiImpactMetric[];
  hero?: boolean;
}) {
  if (hero) {
    return (
      <div className="rounded-2xl border border-[rgba(139,92,246,0.35)] bg-gradient-to-br from-[#121826] via-[#0d111c] to-[#0a1020] p-5 shadow-lg shadow-purple-900/20">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-[#8B5CF6]">Optimization Simulation</p>
            <p className="mt-1 text-lg font-bold text-white">Current State → Optimized State</p>
          </div>
          <div className="flex items-center gap-2 text-xs text-[#94A3B8]">
            <span className="rounded-lg bg-[#1e293b]/80 px-3 py-1.5">Current</span>
            <ArrowDown className="h-4 w-4 rotate-[-90deg] text-[#8B5CF6]" />
            <span className="rounded-lg bg-[#8B5CF6]/20 px-3 py-1.5 text-[#C4B5FD]">Optimized</span>
            <ArrowDown className="h-4 w-4 rotate-[-90deg] text-emerald-400" />
            <span className="rounded-lg bg-emerald-500/15 px-3 py-1.5 text-emerald-400">Expected Result</span>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7">
          {metrics.map((m) => (
            <div
              key={m.label}
              className="rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/80 p-3 transition hover:border-[rgba(139,92,246,0.45)]"
            >
              <p className="text-[10px] font-bold uppercase tracking-wider text-[#64748B]">{m.label}</p>
              <div className="mt-2 flex items-baseline justify-between gap-1">
                <span className="text-sm text-[#94A3B8]">{m.before}</span>
                <ArrowDown className="h-3 w-3 shrink-0 rotate-[-90deg] text-[#64748B]" />
                <span className="text-sm font-semibold text-[#C4B5FD]">{m.after}</span>
              </div>
              <p className="mt-2 text-sm font-bold text-emerald-400">{m.delta}</p>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/60 p-4">
      <table className="w-full min-w-[640px] text-left text-xs">
        <thead className="text-[10px] uppercase tracking-wider text-[#64748B]">
          <tr>
            <th className="pb-3 pr-4">Metric</th>
            <th className="pb-3 pr-4">Current</th>
            <th className="pb-3 pr-4">Optimized</th>
            <th className="pb-3">Delta</th>
          </tr>
        </thead>
        <tbody>
          {metrics.map((m) => (
            <tr key={m.label} className="border-t border-[#2D3748]/40">
              <td className="py-2.5 pr-4 font-semibold text-white">{m.label}</td>
              <td className="py-2.5 pr-4 text-[#94A3B8]">{m.before}</td>
              <td className="py-2.5 pr-4 text-[#C4B5FD]">{m.after}</td>
              <td className="py-2.5 font-semibold text-emerald-400">{m.delta}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const ACTION_ICONS: Record<string, typeof CheckCircle2> = {
  approve: CheckCircle2,
  reject: XCircle,
  simulate: Play,
  report: FileText,
  assign: UserPlus,
};

export function KpiApprovalCenterPanel({ actions }: { actions: KpiApprovalAction[] }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {actions.map((action) => {
        const Icon = ACTION_ICONS[action.id] ?? CheckCircle2;
        return (
          <div
            key={action.id}
            className="rounded-xl border border-[rgba(139,92,246,0.2)] bg-[#121826]/80 p-4 transition hover:border-[rgba(139,92,246,0.45)]"
          >
            <div className="flex items-start gap-2">
              <Icon className="mt-0.5 h-4 w-4 shrink-0 text-[#8B5CF6]" />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-white">{action.label}</p>
                <p className="mt-1 text-xs text-[#94A3B8]">{action.description}</p>
                <p className="mt-2 text-[10px] text-emerald-400">{action.impactHint}</p>
              </div>
            </div>
            <Button
              type="button"
              size="sm"
              variant={action.variant === "danger" ? "destructive" : action.variant === "outline" ? "outline" : "default"}
              className={cn("mt-3 h-7 w-full text-xs", action.variant === "primary" && "bg-[#8B5CF6] hover:bg-[#7C3AED]")}
            >
              {action.label}
            </Button>
          </div>
        );
      })}
    </div>
  );
}
