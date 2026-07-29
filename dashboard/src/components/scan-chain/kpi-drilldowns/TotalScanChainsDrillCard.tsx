"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  PolarAngleAxis,
  RadialBar,
  RadialBarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export interface TotalScanChainsDistributionItem {
  module: string;
  count: number;
}

export interface TotalScanChainsBreakdownItem {
  name: string;
  value: number;
  delta: number;
}

export interface TotalScanChainsLengthBucket {
  range: string;
  value: number;
}

export type DistributionTabId = "Module" | "Product" | "Fab" | "Tester" | "Lot";

export type BreakdownTabId = "Module" | "Scan Chain" | "Product" | "Tester" | "Fab" | "Lot";

export interface TotalScanChainsProps {
  totalChains: number;
  activeChains: number;
  disabledChains: number;
  growth: number;
  businessImpact: string;
  operationalStatus: string;
  distribution: TotalScanChainsDistributionItem[];
  distributionByTab: Record<DistributionTabId, TotalScanChainsDistributionItem[]>;
  compressionRatio: number;
  chainLengthDistribution: TotalScanChainsLengthBucket[];
  breakdown: TotalScanChainsBreakdownItem[];
  breakdownByTab: Record<BreakdownTabId, TotalScanChainsBreakdownItem[]>;
}

const DISTRIBUTION_TABS: DistributionTabId[] = ["Module", "Product", "Fab", "Tester", "Lot"];
const BREAKDOWN_TABS: BreakdownTabId[] = ["Module", "Scan Chain", "Product", "Tester", "Fab", "Lot"];

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

function statusBadgeClass(status: string): string {
  const key = status.toLowerCase();
  if (key === "critical") return "border-red-500/40 bg-red-500/15 text-red-300";
  if (key === "warning") return "border-amber-500/40 bg-amber-500/15 text-amber-300";
  if (key === "monitor") return "border-cyan-500/40 bg-cyan-500/15 text-cyan-300";
  return "border-emerald-500/40 bg-emerald-500/15 text-emerald-300";
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

export function TotalScanChainsDrillCard(props: TotalScanChainsProps) {
  const {
    totalChains,
    activeChains,
    disabledChains,
    growth,
    businessImpact,
    operationalStatus,
    distributionByTab,
    compressionRatio,
    chainLengthDistribution,
    breakdownByTab,
  } = props;

  const [distributionTab, setDistributionTab] = useState<DistributionTabId>("Module");
  const [breakdownTab, setBreakdownTab] = useState<BreakdownTabId>("Module");

  const distributionData = useMemo(
    () => distributionByTab[distributionTab] ?? [],
    [distributionByTab, distributionTab]
  );

  const breakdownData = useMemo(
    () => breakdownByTab[breakdownTab] ?? [],
    [breakdownByTab, breakdownTab]
  );

  const breakdownMax = useMemo(
    () => Math.max(...breakdownData.map((item) => item.value), 1),
    [breakdownData]
  );

  const growthPositive = growth >= 0;
  const gaugeFill = Math.min(Math.max((compressionRatio / 60) * 100, 8), 100);

  const radialData = [{ name: "Compression", value: gaugeFill, fill: "#7C3AED" }];

  return (
    <div className="space-y-8 overflow-x-hidden">
      <motion.section {...sectionMotion} transition={{ duration: 0.35 }}>
        <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-[#A78BFA]">
          Executive Summary
        </h3>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          <SummaryMetricCard label="Total Scan Chains" className="border-[#7C3AED]/35">
            <p className="text-2xl font-bold tabular-nums text-[#A78BFA]">
              {totalChains.toLocaleString()}
            </p>
          </SummaryMetricCard>
          <SummaryMetricCard label="Active Scan Chains" className="border-emerald-500/25">
            <p className="text-2xl font-bold tabular-nums text-emerald-400">
              {activeChains.toLocaleString()}
            </p>
          </SummaryMetricCard>
          <SummaryMetricCard label="Disabled Scan Chains" className="border-red-500/25">
            <p className="text-2xl font-bold tabular-nums text-red-400">
              {disabledChains.toLocaleString()}
            </p>
          </SummaryMetricCard>
          <SummaryMetricCard label="Growth vs Previous Lot">
            <div
              className={cn(
                "flex items-center gap-1.5 text-2xl font-bold tabular-nums",
                growthPositive ? "text-emerald-400" : "text-red-400"
              )}
            >
              {growthPositive ? (
                <ArrowUpRight className="h-5 w-5 shrink-0" aria-hidden />
              ) : (
                <ArrowDownRight className="h-5 w-5 shrink-0" aria-hidden />
              )}
              <span>{formatPct(growth, true)}</span>
            </div>
          </SummaryMetricCard>
          <SummaryMetricCard label="Business Impact">
            <Badge className={cn("text-xs font-medium", impactBadgeClass(businessImpact))}>
              {businessImpact}
            </Badge>
          </SummaryMetricCard>
          <SummaryMetricCard label="Operational Status">
            <Badge className={cn("text-xs font-medium", statusBadgeClass(operationalStatus))}>
              {operationalStatus}
            </Badge>
          </SummaryMetricCard>
        </div>
      </motion.section>

      <motion.section {...sectionMotion} transition={{ duration: 0.35, delay: 0.05 }}>
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-[#A78BFA]">
            Scan Chain Distribution
          </h3>
          <TabStrip tabs={DISTRIBUTION_TABS} active={distributionTab} onChange={setDistributionTab} />
        </div>
        <div className={cn(cardShell, "p-3 sm:p-4")}>
          <div className="h-[260px] w-full min-w-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={distributionData}
                layout="vertical"
                margin={{ top: 4, right: 16, left: 4, bottom: 4 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" horizontal={false} />
                <XAxis type="number" stroke="#64748B" fontSize={11} tickLine={false} />
                <YAxis
                  type="category"
                  dataKey="module"
                  stroke="#64748B"
                  fontSize={11}
                  width={96}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{
                    background: "#111827",
                    border: "1px solid #2D3748",
                    borderRadius: "12px",
                    fontSize: "12px",
                  }}
                  formatter={(value) => [Number(value ?? 0).toLocaleString(), "Chains"]}
                />
                <Bar dataKey="count" radius={[0, 6, 6, 0]} isAnimationActive>
                  {distributionData.map((_, index) => (
                    <Cell key={`dist-${index}`} fill={index % 2 === 0 ? "#7C3AED" : "#8B5CF6"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </motion.section>

      <motion.section {...sectionMotion} transition={{ duration: 0.35, delay: 0.1 }}>
        <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-[#A78BFA]">
          Engineering Analytics
        </h3>
        <div className="grid gap-4 lg:grid-cols-2">
          <div className={cardShell}>
            <p className="mb-3 text-sm font-medium text-white">Chain Length Distribution</p>
            <div className="h-[240px] w-full min-w-0">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chainLengthDistribution} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" vertical={false} />
                  <XAxis dataKey="range" stroke="#64748B" fontSize={11} tickLine={false} />
                  <YAxis stroke="#64748B" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      background: "#111827",
                      border: "1px solid #2D3748",
                      borderRadius: "12px",
                      fontSize: "12px",
                    }}
                  />
                  <Bar dataKey="value" fill="#06B6D4" radius={[6, 6, 0, 0]} isAnimationActive />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className={cn(cardShell, "flex flex-col items-center justify-center")}>
            <p className="mb-2 self-start text-sm font-medium text-white">Average Compression Ratio</p>
            <div className="relative h-[220px] w-full min-w-0">
              <ResponsiveContainer width="100%" height="100%">
                <RadialBarChart
                  cx="50%"
                  cy="50%"
                  innerRadius="68%"
                  outerRadius="100%"
                  barSize={14}
                  data={radialData}
                  startAngle={220}
                  endAngle={-40}
                >
                  <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
                  <RadialBar dataKey="value" cornerRadius={8} background={{ fill: "#1E293B" }} />
                </RadialBarChart>
              </ResponsiveContainer>
              <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                <p className="text-3xl font-bold tabular-nums text-[#A78BFA]">
                  {compressionRatio.toFixed(1)} : 1
                </p>
              </div>
            </div>
          </div>
        </div>
      </motion.section>

      <motion.section {...sectionMotion} transition={{ duration: 0.35, delay: 0.15 }}>
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-[#A78BFA]">
            Breakdown Analysis
          </h3>
          <TabStrip tabs={BREAKDOWN_TABS} active={breakdownTab} onChange={setBreakdownTab} />
        </div>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {breakdownData.map((item) => {
            const deltaPositive = item.delta >= 0;
            const progress = (item.value / breakdownMax) * 100;
            return (
              <div key={`${breakdownTab}-${item.name}`} className={cardShell}>
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm font-semibold text-white">{item.name}</p>
                  <span
                    className={cn(
                      "text-xs font-semibold tabular-nums",
                      deltaPositive ? "text-emerald-400" : "text-red-400"
                    )}
                  >
                    {formatPct(item.delta, true)}
                  </span>
                </div>
                <p className="mt-2 text-2xl font-bold tabular-nums text-[#E2E8F0]">
                  {item.value.toLocaleString()}
                </p>
                <div className="mt-3 h-2 overflow-hidden rounded-full bg-[#1E293B]">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-[#7C3AED] to-[#A78BFA] transition-all duration-500"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </motion.section>
    </div>
  );
}
