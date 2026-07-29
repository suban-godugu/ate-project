"use client";

import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { Area, AreaChart, ResponsiveContainer } from "recharts";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { resolveKpiIcon } from "@/components/common/kpiIcons";
import type { KPIStatusVariant, UnifiedKPI } from "@/types/kpi";

export type KPITrendDirection = "positive" | "negative" | "neutral";
export type KPIStatusColor = "positive" | "negative" | "warning" | "neutral" | "ai";
export type EnterpriseKPIGridVariant = "overview" | "section";

export interface EnterpriseKPICardProps {
  icon: string | LucideIcon;
  title: string;
  value: string;
  subtitle?: string;
  trend: string;
  trendDirection?: KPITrendDirection;
  badge: string;
  sparkline?: number[];
  statusColor?: KPIStatusColor;
  loading?: boolean;
  error?: boolean;
  empty?: boolean;
  onRetry?: () => void;
  onClick?: () => void;
  index?: number;
  id?: string;
  showSparkline?: boolean;
  "aria-label"?: string;
}

/** @deprecated Use EnterpriseKPICardProps */
export type KPICardProps = EnterpriseKPICardProps;

const CARD_SHELL =
  "h-[220px] min-h-[220px] max-h-[220px] w-full min-w-0";

const CARD_SURFACE =
  "flex h-full w-full flex-col rounded-[18px] border border-[rgba(124,58,237,0.25)] bg-[#111827] p-[22px] shadow-sm transition-all duration-200";

const badgeStyles: Record<KPIStatusColor, string> = {
  positive: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
  negative: "border-red-500/30 bg-red-500/10 text-red-400",
  warning: "border-amber-500/30 bg-amber-500/10 text-amber-400",
  neutral: "border-cyan-500/30 bg-cyan-500/10 text-cyan-400",
  ai: "border-[#7C3AED]/30 bg-[#7C3AED]/10 text-[#A78BFA]",
};

const trendStyles: Record<KPITrendDirection, string> = {
  positive: "text-[#10B981]",
  negative: "text-[#EF4444]",
  neutral: "text-[#64748B]",
};

function variantToStatusColor(variant?: KPIStatusVariant): KPIStatusColor {
  switch (variant) {
    case "success":
      return "positive";
    case "danger":
      return "negative";
    case "warning":
      return "warning";
    case "info":
      return "neutral";
    default:
      return "ai";
  }
}

function resolveTrendDirection(change: number, positiveIsGood: boolean): KPITrendDirection {
  if (change === 0) return "neutral";
  const isPositive = positiveIsGood ? change > 0 : change < 0;
  return isPositive ? "positive" : "negative";
}

function normalizeListStyleValue(kpi: UnifiedKPI): Pick<UnifiedKPI, "value" | "subtitle"> {
  const { value, subtitle } = kpi;

  const bulletCount = value.split("•").map((part) => part.trim()).filter(Boolean).length;
  if (bulletCount > 1 && !subtitle) {
    return {
      value: String(bulletCount),
      subtitle: value,
    };
  }

  const arrowMatch = value.match(/^(.+?)\s*→\s*(.+)$/);
  if (arrowMatch && !subtitle) {
    return {
      value: arrowMatch[2]!.trim(),
      subtitle: `from ${arrowMatch[1]!.trim()}`,
    };
  }

  const slashMatch = value.match(/^([\d,]+)\s*\/\s*([\d,]+)$/);
  if (slashMatch && !subtitle) {
    return {
      value: slashMatch[1]!,
      subtitle: `of ${slashMatch[2]!} total`,
    };
  }

  return { value, subtitle };
}

const KPI_TITLE_CLASS =
  "w-full truncate text-[16px] font-semibold leading-5 text-[#E2E8F0]";

const KPI_VALUE_CLASS =
  "mt-0.5 w-full shrink-0 truncate text-left text-[44px] font-bold leading-[48px] tracking-tight text-white tabular-nums";

const KPI_SUBTITLE_CLASS =
  "mt-1 w-full truncate text-[14px] font-normal leading-5 text-[#94A3B8]";

const KPI_TREND_CLASS =
  "mt-1 w-full truncate text-[15px] font-semibold leading-5";

const KPI_META_SLOT_CLASS = "mt-1 min-h-[20px] w-full";

function KPIValue({ value }: { value: string }) {
  return (
    <motion.p
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={KPI_VALUE_CLASS}
      title={value}
    >
      {value}
    </motion.p>
  );
}

export function kpiPropsFromUnified(kpi: UnifiedKPI): EnterpriseKPICardProps {
  const positiveIsGood = kpi.positiveIsGood ?? true;
  const { value, subtitle } = normalizeListStyleValue(kpi);
  const changeLabel = kpi.change === 0 ? "Stable" : `${kpi.change > 0 ? "+" : ""}${kpi.change}%`;
  const direction = resolveTrendDirection(kpi.change, positiveIsGood);

  return {
    id: kpi.id,
    icon: kpi.icon,
    title: kpi.title,
    value,
    subtitle,
    trend: changeLabel,
    trendDirection: kpi.change === 0 ? "neutral" : direction,
    badge: kpi.status ?? (kpi.change === 0 ? "ACTIVE" : changeLabel),
    sparkline: kpi.sparkline,
    statusColor: kpi.status
      ? variantToStatusColor(kpi.statusVariant)
      : direction === "positive"
        ? "positive"
        : direction === "negative"
          ? "negative"
          : "neutral",
    "aria-label": kpi.description ?? kpi.title,
  };
}

export function EnterpriseKPISkeleton() {
  return (
    <div className={cn(CARD_SHELL, "h-full w-full")} aria-hidden="true">
      <div className={cn(CARD_SURFACE, "animate-pulse")}>
        <div className="mb-2 flex justify-between gap-2">
          <div className="h-12 w-12 shrink-0 rounded-full bg-[#1e293b]" />
          <div className="h-[26px] w-16 shrink-0 rounded-full bg-[#1e293b]" />
        </div>
        <div className="mb-1 h-4 w-24 rounded bg-[#1e293b]" />
        <div className="mb-1 h-12 w-28 rounded bg-[#1e293b]" />
        <div className="mb-2 h-3.5 w-20 rounded bg-[#1e293b]" />
        <div className="mt-auto h-[44px] w-full rounded bg-[#1e293b]" />
      </div>
    </div>
  );
}

/** @deprecated Use EnterpriseKPISkeleton */
export const KPISkeleton = EnterpriseKPISkeleton;

export function EnterpriseKPIEmptyCard({ index = 0 }: { index?: number }) {
  return (
    <EnterpriseKPICard
      icon="inbox"
      title="Metric"
      value="—"
      trend="—"
      trendDirection="neutral"
      badge="N/A"
      statusColor="neutral"
      empty
      index={index}
      showSparkline={false}
      aria-label="No data available"
    />
  );
}

/** @deprecated Use EnterpriseKPIEmptyCard */
export const KPIEmptyCard = EnterpriseKPIEmptyCard;

export function EnterpriseKPICard({
  icon,
  title,
  value,
  subtitle,
  trend,
  trendDirection = "neutral",
  badge,
  sparkline = [],
  statusColor = "ai",
  loading = false,
  error = false,
  empty = false,
  onRetry,
  onClick,
  index = 0,
  id = title,
  showSparkline = true,
  "aria-label": ariaLabel,
}: EnterpriseKPICardProps) {
  if (loading) return <EnterpriseKPISkeleton />;

  const Icon = resolveKpiIcon(icon);
  const clickable = Boolean(onClick);
  const chartData = sparkline.map((v, i) => ({ i, v }));
  const sparkGradientId = `kpi-spark-${id.replace(/\s+/g, "-")}`;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04, duration: 0.2 }}
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
          CARD_SURFACE,
          "group hover:border-[rgba(124,58,237,0.45)] hover:shadow-[0_4px_24px_rgba(124,58,237,0.12)] hover:-translate-y-0.5",
          clickable && "hover:shadow-[0_0_20px_rgba(124,58,237,0.15)]",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#7C3AED]/60"
        )}
      >
        <div className="mb-2 flex shrink-0 items-start justify-between gap-2">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-[#7C3AED]/15 text-[#7C3AED]">
            <Icon className="h-6 w-6" aria-hidden="true" />
          </div>
          <span
            className={cn(
              "inline-flex h-[26px] min-w-0 max-w-[55%] shrink items-center truncate rounded-full border px-3 py-1.5 text-[12px] font-semibold leading-none",
              badgeStyles[statusColor]
            )}
            title={badge}
          >
            {badge}
          </span>
        </div>

        {error ? (
          <div className="flex flex-1 flex-col items-start justify-center gap-2">
            <p className="truncate text-[16px] font-medium text-[#94A3B8]">Unable to load KPI</p>
            {onRetry && (
              <Button type="button" size="sm" variant="outline" className="h-7 text-xs" onClick={onRetry}>
                Retry
              </Button>
            )}
          </div>
        ) : empty ? (
          <div className="flex flex-1 flex-col items-start justify-center">
            <p className="truncate text-[16px] font-medium text-[#94A3B8]">No Data Available</p>
          </div>
        ) : (
          <>
            <div className="min-h-0 w-full flex-1 overflow-hidden">
              <p className={KPI_TITLE_CLASS} title={title}>
                {title}
              </p>
              <KPIValue value={value} />
              <div className={KPI_META_SLOT_CLASS}>
                {subtitle ? (
                  <p className={KPI_SUBTITLE_CLASS} title={subtitle}>
                    {subtitle}
                  </p>
                ) : (
                  <p
                    className={cn(KPI_TREND_CLASS, trendStyles[trendDirection])}
                    title={trend}
                  >
                    {trend}
                  </p>
                )}
              </div>
            </div>

            <div className="mt-auto w-full shrink-0">
              {showSparkline && sparkline.length > 0 ? (
                <div className="h-[44px] w-full min-w-0 opacity-90">
                  <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient id={sparkGradientId} x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#7C3AED" stopOpacity={0.35} />
                          <stop offset="95%" stopColor="#7C3AED" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <Area
                        type="monotone"
                        dataKey="v"
                        stroke="#7C3AED"
                        strokeWidth={1.5}
                        fill={`url(#${sparkGradientId})`}
                        dot={false}
                        isAnimationActive
                        animationDuration={800}
                        animationEasing="ease-out"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="h-[44px] w-full" aria-hidden="true" />
              )}
            </div>
          </>
        )}
      </div>
    </motion.div>
  );
}

/** @deprecated Use EnterpriseKPICard */
export const KPICard = EnterpriseKPICard;

function gridClassForVariant(variant: EnterpriseKPIGridVariant, className?: string) {
  const base = variant === "section" ? "kpi-grid-section" : "kpi-grid";
  return cn(base, "w-full", className);
}

export function EnterpriseKPIGrid<T extends UnifiedKPI>({
  data,
  onCardClick,
  showSparkline = true,
  variant = "overview",
  className,
}: {
  data: T[];
  onCardClick?: (kpi: T) => void;
  showSparkline?: boolean;
  variant?: EnterpriseKPIGridVariant;
  className?: string;
}) {
  if (!data.length) {
    return null;
  }

  return (
    <div className={gridClassForVariant(variant, className)}>
      {data.map((kpi, i) => {
        const props = kpiPropsFromUnified(kpi);
        return (
          <EnterpriseKPICard
            key={kpi.id}
            {...props}
            index={i}
            showSparkline={showSparkline}
            onClick={onCardClick ? () => onCardClick(kpi) : undefined}
          />
        );
      })}
    </div>
  );
}

/** @deprecated Use EnterpriseKPIGrid */
export const KPIGrid = EnterpriseKPIGrid;

export function legacyGridClassToVariant(className?: string): EnterpriseKPIGridVariant {
  if (!className) return "overview";
  if (
    className.includes("kpi-grid-section") ||
    className.includes("ai-rec-kpi-grid") ||
    className.includes("test-opt-kpi-grid")
  ) {
    return "section";
  }
  return "overview";
}
