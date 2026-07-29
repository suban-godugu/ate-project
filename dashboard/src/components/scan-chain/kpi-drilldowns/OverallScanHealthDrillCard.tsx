"use client";

import { motion } from "framer-motion";
import {
  ArrowDownRight,
  ArrowUpRight,
  CircleHelp,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export interface OverallScanHealthBreakdownRow {
  metric: string;
  weight: number;
  score: number;
  contribution: number;
}

export interface OverallScanHealthProps {
  currentHealth: number;
  targetHealth: number;
  trend: number;
  gap: number;
  status: string;
  risk: string;
  businessImpact: string;
  operationalPriority: string;
  healthyChains: number;
  failingChains: number;
  unknownChains: number;
  breakdown: OverallScanHealthBreakdownRow[];
}

const sectionMotion = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
};

const cardShell =
  "rounded-xl border border-[rgba(124,58,237,0.22)] bg-gradient-to-br from-[#121826] to-[#0d111c] p-4 shadow-sm transition duration-200 hover:border-[rgba(139,92,246,0.45)] hover:shadow-[0_0_24px_rgba(124,58,237,0.12)]";

function formatPct(value: number, signed = false): string {
  const prefix = signed && value > 0 ? "+" : "";
  return `${prefix}${value.toFixed(1)}%`;
}

function impactBadgeClass(impact: string): string {
  const key = impact.toLowerCase();
  if (key === "critical") return "border-red-500/40 bg-red-500/15 text-red-300";
  if (key === "high") return "border-orange-500/40 bg-orange-500/15 text-orange-300";
  if (key === "moderate") return "border-amber-500/40 bg-amber-500/15 text-amber-300";
  return "border-emerald-500/40 bg-emerald-500/15 text-emerald-300";
}

function priorityBadgeClass(priority: string): string {
  const key = priority.toLowerCase();
  if (key === "immediate") return "border-red-500/40 bg-red-500/15 text-red-300";
  if (key === "monitor") return "border-amber-500/40 bg-amber-500/15 text-amber-300";
  if (key === "stable") return "border-emerald-500/40 bg-emerald-500/15 text-emerald-300";
  return "border-cyan-500/40 bg-cyan-500/15 text-cyan-300";
}

function SummaryMetricCard({
  label,
  children,
  className,
}: {
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn(cardShell, "min-h-[108px]", className)}>
      <p className="text-[11px] font-medium uppercase tracking-wider text-[#94A3B8]">{label}</p>
      <div className="mt-2">{children}</div>
    </div>
  );
}

export function OverallScanHealthDrillCard(props: OverallScanHealthProps) {
  const {
    currentHealth,
    targetHealth,
    trend,
    gap,
    businessImpact,
    operationalPriority,
    healthyChains,
    failingChains,
    unknownChains,
    breakdown,
  } = props;

  const trendPositive = trend >= 0;
  const gapPositive = gap >= 0;

  return (
    <div className="space-y-8 overflow-x-hidden">
      <motion.section {...sectionMotion} transition={{ duration: 0.35 }}>
        <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-[#A78BFA]">
          Executive Summary
        </h3>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          <SummaryMetricCard label="Current Health">
            <p className="text-2xl font-bold tabular-nums text-white">{formatPct(currentHealth)}</p>
          </SummaryMetricCard>
          <SummaryMetricCard label="Target">
            <p className="text-2xl font-bold tabular-nums text-white">{formatPct(targetHealth)}</p>
          </SummaryMetricCard>
          <SummaryMetricCard label="Gap">
            <p
              className={cn(
                "text-2xl font-bold tabular-nums",
                gapPositive ? "text-emerald-400" : "text-red-400"
              )}
            >
              {formatPct(gap, true)}
            </p>
          </SummaryMetricCard>
          <SummaryMetricCard label="Trend">
            <div
              className={cn(
                "flex items-center gap-1.5 text-2xl font-bold tabular-nums",
                trendPositive ? "text-emerald-400" : "text-red-400"
              )}
            >
              {trendPositive ? (
                <ArrowUpRight className="h-5 w-5 shrink-0" aria-hidden />
              ) : (
                <ArrowDownRight className="h-5 w-5 shrink-0" aria-hidden />
              )}
              <span>{formatPct(trend, true)}</span>
            </div>
          </SummaryMetricCard>
          <SummaryMetricCard label="Business Impact">
            <Badge className={cn("text-xs font-medium", impactBadgeClass(businessImpact))}>
              {businessImpact}
            </Badge>
          </SummaryMetricCard>
          <SummaryMetricCard label="Operational Priority">
            <Badge className={cn("text-xs font-medium", priorityBadgeClass(operationalPriority))}>
              {operationalPriority}
            </Badge>
          </SummaryMetricCard>
        </div>
      </motion.section>

      <motion.section {...sectionMotion} transition={{ duration: 0.35, delay: 0.05 }}>
        <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-[#A78BFA]">
          Health Score Breakdown
        </h3>
        <div className={cn(cardShell, "overflow-hidden p-0")}>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[520px] text-left text-sm">
              <thead>
                <tr className="border-b border-[#2D3748]/80 bg-[#0B0F1A]/60 text-[11px] uppercase tracking-wider text-[#94A3B8]">
                  <th className="px-4 py-3 font-medium">Metric</th>
                  <th className="px-4 py-3 font-medium">Weight</th>
                  <th className="px-4 py-3 font-medium">Score</th>
                  <th className="px-4 py-3 font-medium">Contribution</th>
                </tr>
              </thead>
              <tbody>
                {breakdown.map((row) => (
                  <tr
                    key={row.metric}
                    className="border-b border-[#2D3748]/50 text-[#CBD5E1] last:border-b-0 hover:bg-white/[0.02]"
                  >
                    <td className="px-4 py-3 font-medium text-white">{row.metric}</td>
                    <td className="px-4 py-3 tabular-nums">{row.weight}%</td>
                    <td className="px-4 py-3 tabular-nums">{row.score}%</td>
                    <td className="px-4 py-3 tabular-nums text-[#A78BFA]">{row.contribution.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="border-t border-[#2D3748]/80 bg-[#0B0F1A]/40 px-4 py-5">
            <p className="text-xs font-medium uppercase tracking-wider text-[#94A3B8]">
              Final Overall Scan Health
            </p>
            <p className="mt-1 text-3xl font-bold tabular-nums text-[#A78BFA] sm:text-4xl">
              {formatPct(currentHealth)}
            </p>
          </div>
        </div>
      </motion.section>

      <motion.section {...sectionMotion} transition={{ duration: 0.35, delay: 0.1 }}>
        <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-[#A78BFA]">
          Healthy vs Failing Chains
        </h3>
        <div className="grid gap-3 md:grid-cols-3">
          <div className={cn(cardShell, "border-emerald-500/25")}>
            <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500/15 text-emerald-400">
              <ShieldCheck className="h-5 w-5" aria-hidden />
            </div>
            <p className="text-[11px] font-medium uppercase tracking-wider text-[#94A3B8]">
              Healthy Chains
            </p>
            <p className="mt-2 text-3xl font-bold tabular-nums text-emerald-400">
              {healthyChains.toLocaleString()}
            </p>
          </div>
          <div className={cn(cardShell, "border-red-500/25")}>
            <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-red-500/15 text-red-400">
              <ShieldAlert className="h-5 w-5" aria-hidden />
            </div>
            <p className="text-[11px] font-medium uppercase tracking-wider text-[#94A3B8]">
              Failing Chains
            </p>
            <p className="mt-2 text-3xl font-bold tabular-nums text-red-400">
              {failingChains.toLocaleString()}
            </p>
          </div>
          <div className={cn(cardShell, "border-amber-500/25")}>
            <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-amber-500/15 text-amber-400">
              <CircleHelp className="h-5 w-5" aria-hidden />
            </div>
            <p className="text-[11px] font-medium uppercase tracking-wider text-[#94A3B8]">Unknown</p>
            <p className="mt-2 text-3xl font-bold tabular-nums text-amber-400">
              {unknownChains.toLocaleString()}
            </p>
          </div>
        </div>
      </motion.section>
    </div>
  );
}
