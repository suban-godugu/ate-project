"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export interface FailingChainsBreakdownItem {
  category: string;
  name: string;
  failingChains: number;
  delta: number;
  share: number;
}

export interface FailingChainsStatus {
  critical: number;
  active: number;
  underInvestigation: number;
}

export type BreakdownTabId = "Scan Chain" | "Pattern" | "Lot" | "Wafer" | "Tester" | "Module";

export interface FailingChainsProps {
  failingChains: number;
  failureRatio: number;
  newlyDetectedFailures: number;
  changeVsPreviousLot: number;
  businessImpact: string;
  operationalStatus: string;
  failureStatus: FailingChainsStatus;
  breakdown: FailingChainsBreakdownItem[];
  breakdownByTab: Record<BreakdownTabId, FailingChainsBreakdownItem[]>;
}

const BREAKDOWN_TABS: BreakdownTabId[] = ["Scan Chain", "Pattern", "Lot", "Wafer", "Tester", "Module"];

const STATUS_COLORS = {
  critical: "#EF4444",
  active: "#F97316",
  investigation: "#EAB308",
};

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

function operationalBadgeClass(status: string): string {
  const key = status.toLowerCase();
  if (key === "critical" || key === "fab hold") return "border-red-500/40 bg-red-500/15 text-red-300";
  if (key === "warning") return "border-amber-500/40 bg-amber-500/15 text-amber-300";
  if (key === "monitor") return "border-cyan-500/40 bg-cyan-500/15 text-cyan-300";
  return "border-orange-500/40 bg-orange-500/15 text-orange-300";
}

function TabStrip<T extends string>({
  tabs,
  active,
  onChange,
}: {
  tabs: readonly T[];
  active: T;
  onChange: (tab: T) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {tabs.map((tab) => (
        <button
          key={tab}
          type="button"
          onClick={() => onChange(tab)}
          className={cn(
            "rounded-lg border px-3 py-1.5 text-xs font-medium transition",
            active === tab
              ? "border-[#7C3AED]/50 bg-[#7C3AED]/20 text-[#C4B5FD]"
              : "border-[#2D3748] bg-[#0B0F1A]/60 text-[#94A3B8] hover:border-[#7C3AED]/30 hover:text-white"
          )}
        >
          {tab}
        </button>
      ))}
    </div>
  );
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

export function FailingChainsDrillCard(props: FailingChainsProps) {
  const {
    failingChains,
    failureRatio,
    newlyDetectedFailures,
    changeVsPreviousLot,
    businessImpact,
    operationalStatus,
    failureStatus,
    breakdownByTab,
  } = props;

  const [breakdownTab, setBreakdownTab] = useState<BreakdownTabId>("Scan Chain");

  const breakdownData = useMemo(
    () => breakdownByTab[breakdownTab] ?? [],
    [breakdownByTab, breakdownTab]
  );

  const statusPieData = useMemo(
    () => [
      { name: "Critical Failures", value: failureStatus.critical, color: STATUS_COLORS.critical },
      { name: "Active Failures", value: failureStatus.active, color: STATUS_COLORS.active },
      {
        name: "Under Investigation",
        value: failureStatus.underInvestigation,
        color: STATUS_COLORS.investigation,
      },
    ],
    [failureStatus]
  );

  const statusTotal =
    failureStatus.critical + failureStatus.active + failureStatus.underInvestigation;
  const changePositive = changeVsPreviousLot >= 0;

  return (
    <div className="space-y-8 overflow-x-hidden">
      <motion.section {...sectionMotion} transition={{ duration: 0.35 }}>
        <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-[#A78BFA]">
          Executive Summary
        </h3>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          <SummaryMetricCard label="Failing Chains" className="border-red-500/30">
            <p className="text-2xl font-bold tabular-nums text-red-400">
              {failingChains.toLocaleString()}
            </p>
          </SummaryMetricCard>
          <SummaryMetricCard label="Failure Ratio">
            <p className="text-2xl font-bold tabular-nums text-white">{formatPct(failureRatio)}</p>
          </SummaryMetricCard>
          <SummaryMetricCard label="Newly Detected Failures" className="border-orange-500/25">
            <p className="text-2xl font-bold tabular-nums text-orange-400">
              {newlyDetectedFailures.toLocaleString()}
            </p>
          </SummaryMetricCard>
          <SummaryMetricCard label="Change vs Previous Lot">
            <div
              className={cn(
                "flex items-center gap-1.5 text-2xl font-bold tabular-nums",
                changePositive ? "text-emerald-400" : "text-red-400"
              )}
            >
              {changePositive ? (
                <ArrowUpRight className="h-5 w-5 shrink-0" aria-hidden />
              ) : (
                <ArrowDownRight className="h-5 w-5 shrink-0" aria-hidden />
              )}
              <span>{formatPct(changeVsPreviousLot, true)}</span>
            </div>
          </SummaryMetricCard>
          <SummaryMetricCard label="Business Impact">
            <Badge className={cn("text-xs font-medium", impactBadgeClass(businessImpact))}>
              {businessImpact}
            </Badge>
          </SummaryMetricCard>
          <SummaryMetricCard label="Operational Status">
            <Badge className={cn("text-xs font-medium", operationalBadgeClass(operationalStatus))}>
              {operationalStatus}
            </Badge>
          </SummaryMetricCard>
        </div>
      </motion.section>

      <motion.section {...sectionMotion} transition={{ duration: 0.35, delay: 0.05 }}>
        <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-[#A78BFA]">
          Failure Status
        </h3>
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.35 }}
          className={cn(cardShell, "grid gap-4 lg:grid-cols-[1.2fr_1fr]")}
        >
          <div className="relative h-[280px] w-full min-w-0">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={statusPieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={72}
                  outerRadius={104}
                  paddingAngle={3}
                  dataKey="value"
                  stroke="none"
                  isAnimationActive
                  label={({ name, percent }) =>
                    `${(name ?? "").split(" ")[0]} ${((percent ?? 0) * 100).toFixed(0)}%`
                  }
                  labelLine={false}
                >
                  {statusPieData.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: "#111827",
                    border: "1px solid #2D3748",
                    borderRadius: "12px",
                    fontSize: "12px",
                  }}
                  formatter={(value, name) => {
                    const num = Number(value ?? 0);
                    const pct = statusTotal > 0 ? ((num / statusTotal) * 100).toFixed(1) : "0.0";
                    return [`${num.toLocaleString()} (${pct}%)`, name];
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
              <p className="text-2xl font-bold text-white">{failingChains.toLocaleString()}</p>
              <p className="text-xs text-slate-400">Failing Chains</p>
            </div>
          </div>
          <div className="flex flex-col justify-center gap-3">
            {statusPieData.map((item) => (
              <div
                key={item.name}
                className="flex items-center justify-between rounded-lg border border-[#2D3748]/80 bg-[#0B0F1A]/50 px-3 py-2.5"
              >
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                  <span className="text-sm text-[#CBD5E1]">{item.name}</span>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold tabular-nums text-white">
                    {item.value.toLocaleString()}
                  </p>
                  <p className="text-[11px] text-[#94A3B8]">
                    {statusTotal > 0 ? ((item.value / statusTotal) * 100).toFixed(1) : 0}%
                  </p>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </motion.section>

      <motion.section {...sectionMotion} transition={{ duration: 0.35, delay: 0.1 }}>
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-[#A78BFA]">
            Breakdown Analysis
          </h3>
          <TabStrip tabs={BREAKDOWN_TABS} active={breakdownTab} onChange={setBreakdownTab} />
        </div>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {breakdownData.map((item) => {
            const deltaPositive = item.delta >= 0;
            return (
              <motion.div
                key={`${breakdownTab}-${item.name}`}
                whileHover={{ y: -2 }}
                className={cardShell}
              >
                <p className="text-sm font-semibold text-white">{item.name}</p>
                <p className="mt-2 text-2xl font-bold tabular-nums text-red-400">
                  {item.failingChains.toLocaleString()}
                  <span className="ml-1 text-xs font-medium text-[#94A3B8]">Failing Chains</span>
                </p>
                <div className="mt-2 flex items-center justify-between text-xs">
                  <span
                    className={cn(
                      "font-semibold tabular-nums",
                      deltaPositive ? "text-emerald-400" : "text-red-400"
                    )}
                  >
                    {formatPct(item.delta, true)}
                  </span>
                  <span className="font-medium text-[#A78BFA]">{item.share.toFixed(1)}% Share</span>
                </div>
                <div className="mt-3 h-2 overflow-hidden rounded-full bg-[#1E293B]">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-red-500 to-orange-500 transition-all duration-500"
                    style={{ width: `${Math.min(item.share, 100)}%` }}
                  />
                </div>
              </motion.div>
            );
          })}
        </div>
      </motion.section>
    </div>
  );
}
