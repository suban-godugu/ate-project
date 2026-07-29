"use client";

import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { useEffect } from "react";
import { Area, AreaChart, ResponsiveContainer } from "recharts";
import { resolveKpiIcon } from "@/components/common/kpiIcons";
import { cn } from "@/lib/utils";

export type ExecutiveKPITheme = "dark" | "light";
export type ExecutiveKPITrendDirection = "positive" | "negative" | "neutral";

export interface ExecutiveKPICardProps {
  id: string;
  icon: string | LucideIcon;
  title: string;
  value: string;
  subtitle?: string;
  change: number;
  positiveIsGood?: boolean;
  sparkline?: number[];
  theme?: ExecutiveKPITheme;
  index?: number;
  onClick?: () => void;
  "aria-label"?: string;
}

const CARD_SHELL = "h-[220px] min-h-[220px] max-h-[220px] w-full min-w-0";

function resolveTrendDirection(change: number, positiveIsGood: boolean): ExecutiveKPITrendDirection {
  if (change === 0) return "neutral";
  const isPositive = positiveIsGood ? change > 0 : change < 0;
  return isPositive ? "positive" : "negative";
}

function trendLabel(change: number): string {
  if (change === 0) return "Stable";
  return `${change > 0 ? "+" : ""}${change}% vs prior cycle`;
}

function parseNumericValue(raw: string): { target: number; prefix: string; suffix: string } | null {
  const trimmed = raw.trim();
  const match = trimmed.match(/^([^0-9.-]*)([\d,]+(?:\.\d+)?)(.*)$/);
  if (!match) return null;
  const target = parseFloat(match[2]!.replace(/,/g, ""));
  if (Number.isNaN(target)) return null;
  return { target, prefix: match[1] ?? "", suffix: match[3] ?? "" };
}

function AnimatedMetric({ value, theme = "dark" }: { value: string; theme?: ExecutiveKPITheme }) {
  const parsed = parseNumericValue(value);
  const motionVal = useMotionValue(0);
  const spring = useSpring(motionVal, { duration: 0.4, bounce: 0 });
  const display = useTransform(spring, (v) => {
    if (!parsed) return value;
    const decimals = parsed.target % 1 !== 0 ? 1 : 0;
    const formatted = parsed.target >= 1000 ? Math.round(v).toLocaleString() : v.toFixed(decimals);
    return `${parsed.prefix}${formatted}${parsed.suffix}`;
  });

  useEffect(() => {
    if (parsed) motionVal.set(parsed.target);
  }, [motionVal, parsed, value]);

  return (
    <motion.p
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={cn(
        "mt-0.5 w-full truncate text-left text-[44px] font-bold leading-[48px] tracking-tight tabular-nums",
        theme === "light" ? "text-slate-900" : "text-white"
      )}
    >
      {parsed ? <motion.span>{display}</motion.span> : value}
    </motion.p>
  );
}

const trendBadgeStyles: Record<ExecutiveKPITrendDirection, string> = {
  positive: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
  negative: "border-red-500/30 bg-red-500/10 text-red-400",
  neutral: "border-slate-500/30 bg-slate-500/10 text-slate-300",
};

const trendTextStyles: Record<ExecutiveKPITrendDirection, string> = {
  positive: "text-emerald-400",
  negative: "text-red-400",
  neutral: "text-slate-400",
};

const themeStyles: Record<
  ExecutiveKPITheme,
  { surface: string; iconWrap: string; iconColor: string }
> = {
  dark: {
    surface:
      "border-[rgba(139,92,246,0.25)] bg-gradient-to-br from-[#121826] via-[#121826] to-[#0d111c] shadow-[inset_0_1px_0_rgba(139,92,246,0.06)]",
    iconWrap: "bg-[rgba(124,58,237,0.18)] text-[#8B5CF6]",
    iconColor: "text-[#8B5CF6]",
  },
  light: {
    surface:
      "border-[rgba(139,92,246,0.2)] bg-gradient-to-br from-white via-slate-50 to-slate-100 shadow-sm",
    iconWrap: "bg-[rgba(124,58,237,0.12)] text-[#7C3AED]",
    iconColor: "text-[#7C3AED]",
  },
};

export function ExecutiveKPICard({
  id,
  icon,
  title,
  value,
  subtitle,
  change,
  positiveIsGood = true,
  sparkline = [],
  theme = "dark",
  index = 0,
  onClick,
  "aria-label": ariaLabel,
}: ExecutiveKPICardProps) {
  const Icon = resolveKpiIcon(icon);
  const tokens = themeStyles[theme];
  const direction = resolveTrendDirection(change, positiveIsGood);
  const badge = `${change >= 0 ? "+" : ""}${change}%`;
  const trend = trendLabel(change);
  const chartData = sparkline.map((v, i) => ({ i, v }));
  const sparkGradientId = `exec-kpi-spark-${id.replace(/\s+/g, "-")}`;
  const clickable = Boolean(onClick);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04, duration: 0.25 }}
      className={cn(CARD_SHELL, "h-full w-full", clickable && "cursor-pointer")}
      onClick={onClick}
      role={clickable ? "button" : undefined}
      tabIndex={clickable ? 0 : undefined}
      aria-label={ariaLabel ?? title}
      onKeyDown={(e) => {
        if (clickable && (e.key === "Enter" || e.key === " ")) {
          e.preventDefault();
          onClick?.();
        }
      }}
    >
      <div
        className={cn(
          "group relative flex h-full w-full flex-col rounded-[18px] border p-[22px] transition-all duration-300",
          tokens.surface,
          clickable &&
            "hover:-translate-y-1 hover:border-[rgba(139,92,246,0.45)] hover:shadow-[0_12px_40px_rgba(139,92,246,0.18)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#8B5CF6]/50"
        )}
      >
        <div className="pointer-events-none absolute -right-6 -top-6 h-24 w-24 rounded-full bg-[#8B5CF6]/10 blur-2xl" aria-hidden="true" />

        {/* Row 1 — icon + badge */}
        <div className="relative mb-2 flex shrink-0 items-start justify-between gap-2">
          <div className={cn("flex h-12 w-12 shrink-0 items-center justify-center rounded-full", tokens.iconWrap)}>
            <Icon className={cn("h-6 w-6", tokens.iconColor)} aria-hidden="true" />
          </div>
          <span
            className={cn(
              "inline-flex h-[26px] shrink-0 items-center rounded-full border px-3 text-[12px] font-semibold leading-none",
              trendBadgeStyles[direction]
            )}
          >
            {badge}
          </span>
        </div>

        {/* Row 2–4 — title, value, meta (matches EnterpriseKPICard flow) */}
        <div className="relative min-h-0 w-full flex-1 overflow-hidden">
          <p
            className={cn(
              "w-full truncate text-[16px] font-semibold leading-5",
              theme === "light" ? "text-slate-700" : "text-white"
            )}
            title={title}
          >
            {title}
          </p>
          <AnimatedMetric value={value} theme={theme} />
          <div className="mt-1 min-h-[20px] w-full">
            {subtitle ? (
              <p
                className={cn(
                  "w-full truncate text-[14px] leading-5",
                  theme === "light" ? "text-slate-500" : "text-[#CBD5E1]"
                )}
                title={subtitle}
              >
                {subtitle}
              </p>
            ) : (
              <p className={cn("w-full truncate text-[14px] font-medium leading-5", trendTextStyles[direction])} title={trend}>
                {trend}
              </p>
            )}
          </div>
        </div>

        {/* Row 5 — sparkline */}
        <div className="relative mt-auto w-full shrink-0">
          {sparkline.length > 0 ? (
            <div className="h-[44px] w-full min-w-0 opacity-90">
              <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id={sparkGradientId} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.35} />
                      <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <Area
                    type="monotone"
                    dataKey="v"
                    stroke="#8B5CF6"
                    strokeWidth={1.5}
                    fill={`url(#${sparkGradientId})`}
                    dot={false}
                    isAnimationActive
                    animationDuration={900}
                    animationEasing="ease-out"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-[44px] w-full" aria-hidden="true" />
          )}
        </div>
      </div>
    </motion.div>
  );
}
