"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export interface HealthyChainsDistributionItem {
  category: string;
  name: string;
  value: number;
  percentage: number;
}

export interface HealthyChainsBreakdownItem {
  category: string;
  name: string;
  healthyChains: number;
  delta: number;
  share: number;
}

export interface HealthyChainsStatus {
  healthy: number;
  recovered: number;
  monitoring: number;
}

export interface HealthyChainsDiagnosis {
  confidence: number;
  summary: string;
  healthFactors: string[];
  healthyComponents: string[];
}

export type DistributionTabId = "Module" | "Product" | "Fab" | "Tester" | "Lot" | "Wafer";
export type BreakdownTabId = DistributionTabId;

export interface HealthyChainsProps {
  healthyChains: number;
  healthyRatio: number;
  recoveredChains: number;
  growth: number;
  businessImpact: string;
  operationalStatus: string;
  distribution: HealthyChainsDistributionItem[];
  distributionByTab: Record<DistributionTabId, HealthyChainsDistributionItem[]>;
  status: HealthyChainsStatus;
  breakdown: HealthyChainsBreakdownItem[];
  breakdownByTab: Record<BreakdownTabId, HealthyChainsBreakdownItem[]>;
  diagnosis: HealthyChainsDiagnosis;
}

const DISTRIBUTION_TABS: DistributionTabId[] = ["Module", "Product", "Fab", "Tester", "Lot", "Wafer"];
const BREAKDOWN_TABS: BreakdownTabId[] = [...DISTRIBUTION_TABS];

const STATUS_COLORS = {
  healthy: "#22C55E",
  recovered: "#EAB308",
  monitoring: "#3B82F6",
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

export function HealthyChainsDrillCard(props: HealthyChainsProps) {
  const {
    healthyChains,
    healthyRatio,
    recoveredChains,
    growth,
    businessImpact,
    operationalStatus,
    distributionByTab,
    status,
    breakdownByTab,
    diagnosis,
  } = props;

  const [distributionTab, setDistributionTab] = useState<DistributionTabId>("Module");
  const [breakdownTab, setBreakdownTab] = useState<BreakdownTabId>("Lot");
  const [activeComponent, setActiveComponent] = useState<string | null>(null);

  const distributionData = useMemo(() => {
    const items = [...(distributionByTab[distributionTab] ?? [])];
    return items.sort((a, b) => b.value - a.value);
  }, [distributionByTab, distributionTab]);

  const breakdownData = useMemo(
    () => breakdownByTab[breakdownTab] ?? [],
    [breakdownByTab, breakdownTab]
  );

  const statusPieData = useMemo(
    () => [
      { name: "Healthy", value: status.healthy, color: STATUS_COLORS.healthy },
      { name: "Recovered", value: status.recovered, color: STATUS_COLORS.recovered },
      { name: "Under Monitoring", value: status.monitoring, color: STATUS_COLORS.monitoring },
    ],
    [status]
  );

  const statusTotal = status.healthy + status.recovered + status.monitoring;
  const growthPositive = growth >= 0;

  return (
    <div className="space-y-8 overflow-x-hidden">
      <motion.section {...sectionMotion} transition={{ duration: 0.35 }}>
        <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-[#A78BFA]">
          Executive Summary
        </h3>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          <SummaryMetricCard label="Healthy Chains" className="border-emerald-500/25">
            <p className="text-2xl font-bold tabular-nums text-emerald-400">
              {healthyChains.toLocaleString()}
            </p>
          </SummaryMetricCard>
          <SummaryMetricCard label="Healthy Ratio">
            <p className="text-2xl font-bold tabular-nums text-white">{formatPct(healthyRatio)}</p>
          </SummaryMetricCard>
          <SummaryMetricCard label="Newly Recovered Chains" className="border-emerald-500/20">
            <p className="text-2xl font-bold tabular-nums text-emerald-300">
              {recoveredChains.toLocaleString()}
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
            Healthy Chain Distribution
          </h3>
          <TabStrip tabs={DISTRIBUTION_TABS} active={distributionTab} onChange={setDistributionTab} />
        </div>
        <motion.div
          key={distributionTab}
          initial={{ opacity: 0, x: 8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
          className={cn(cardShell, "p-3 sm:p-4")}
        >
          <div className="h-[280px] w-full min-w-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={distributionData}
                layout="vertical"
                margin={{ top: 4, right: 56, left: 4, bottom: 4 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" horizontal={false} />
                <XAxis type="number" stroke="#64748B" fontSize={11} tickLine={false} />
                <YAxis
                  type="category"
                  dataKey="name"
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
                  formatter={(value, _name, item) => {
                    const pct = (item?.payload as HealthyChainsDistributionItem | undefined)?.percentage;
                    return [`${Number(value ?? 0).toLocaleString()} (${pct?.toFixed(1)}%)`, "Healthy Chains"];
                  }}
                />
                <Bar dataKey="value" radius={[0, 6, 6, 0]} isAnimationActive>
                  {distributionData.map((_, index) => (
                    <Cell key={`healthy-dist-${index}`} fill={index === 0 ? "#22C55E" : "#16A34A"} />
                  ))}
                  <LabelList
                    dataKey="percentage"
                    position="right"
                    formatter={(value) => `${Number(value).toFixed(1)}%`}
                    className="fill-[#94A3B8] text-[11px]"
                  />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </motion.section>

      <motion.section {...sectionMotion} transition={{ duration: 0.35, delay: 0.1 }}>
        <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-[#A78BFA]">
          Healthy Chain Status
        </h3>
        <div className={cn(cardShell, "grid gap-4 lg:grid-cols-[1.2fr_1fr]")}>
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
              <p className="text-2xl font-bold text-white">{statusTotal.toLocaleString()}</p>
              <p className="text-xs text-slate-400">Total Tracked</p>
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
            return (
              <motion.div
                key={`${breakdownTab}-${item.name}`}
                whileHover={{ y: -2 }}
                className={cardShell}
              >
                <p className="text-sm font-semibold text-white">{item.name}</p>
                <p className="mt-2 text-2xl font-bold tabular-nums text-emerald-400">
                  {item.healthyChains.toLocaleString()}
                  <span className="ml-1 text-xs font-medium text-[#94A3B8]">Healthy Chains</span>
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
                    className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-[#7C3AED] transition-all duration-500"
                    style={{ width: `${Math.min(item.share, 100)}%` }}
                  />
                </div>
              </motion.div>
            );
          })}
        </div>
      </motion.section>

      <motion.section {...sectionMotion} transition={{ duration: 0.35, delay: 0.2 }}>
        <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-[#A78BFA]">
          Health Diagnosis
        </h3>
        <div className={cn(cardShell, "space-y-4")}>
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-sm font-medium text-[#94A3B8]">Confidence</span>
            <Badge className="border-emerald-500/40 bg-emerald-500/15 text-sm font-semibold text-emerald-300">
              {diagnosis.confidence}%
            </Badge>
          </div>
          <div>
            <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[#94A3B8]">
              Diagnosis
            </p>
            <p className="text-sm leading-relaxed text-[#CBD5E1]">{diagnosis.summary}</p>
          </div>
          <div>
            <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[#94A3B8]">
              Health Factors
            </p>
            <div className="flex flex-wrap gap-2">
              {diagnosis.healthFactors.map((factor) => (
                <Badge
                  key={factor}
                  className="border-[#7C3AED]/30 bg-[#7C3AED]/10 text-[11px] text-[#C4B5FD]"
                >
                  {factor}
                </Badge>
              ))}
            </div>
          </div>
          <div>
            <p className="mb-2 text-xs font-medium uppercase tracking-wider text-[#94A3B8]">
              Healthy Components
            </p>
            <div className="flex flex-wrap gap-2">
              {diagnosis.healthyComponents.map((component) => (
                <button
                  key={component}
                  type="button"
                  onClick={() => setActiveComponent(component)}
                  className={cn(
                    "rounded-lg border px-3 py-1.5 text-xs font-medium transition",
                    activeComponent === component
                      ? "border-emerald-500/50 bg-emerald-500/15 text-emerald-300"
                      : "border-[#2D3748] bg-[#0B0F1A]/60 text-[#94A3B8] hover:border-emerald-500/30 hover:text-white"
                  )}
                >
                  {component}
                </button>
              ))}
            </div>
          </div>
        </div>
      </motion.section>
    </div>
  );
}
