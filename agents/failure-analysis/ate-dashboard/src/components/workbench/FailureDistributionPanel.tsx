"use client";

import { memo, useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  Treemap,
  XAxis,
  YAxis,
} from "recharts";
import type { DashboardCharts } from "@/stores/analysisStore";
import type { DetectedPattern } from "@/lib/api";

const COLORS = ["#7C3AED", "#38bdf8", "#f472b6", "#34d399", "#fbbf24", "#fb7185"];

type Props = {
  charts: DashboardCharts | null;
  patterns: DetectedPattern[];
};

export const FailureDistributionPanel = memo(function FailureDistributionPanel({
  charts,
  patterns,
}: Props) {
  const categories = useMemo(() => {
    const fromCharts = (charts?.category_distribution || []).filter((row) => row.count > 0);
    if (fromCharts.length) return fromCharts;

    const counts = new Map<string, number>();
    for (const pattern of patterns) {
      const label =
        pattern.pattern_category || pattern.pattern_name || pattern.pattern_id || "unknown";
      counts.set(label, (counts.get(label) || 0) + (pattern.failure_count || 1));
    }
    return [...counts.entries()].map(([category, count]) => ({ category, count }));
  }, [charts?.category_distribution, patterns]);
  const distribution =
    charts?.failure_distribution?.length
      ? charts.failure_distribution
      : patterns.map((p) => ({
          name: p.pattern_name || p.pattern_id,
          count: p.failure_count,
        }));

  const treemapData = useMemo(
    () =>
      categories.map((c) => ({
        name: c.category,
        size: c.count,
        fill: COLORS[categories.indexOf(c) % COLORS.length],
      })),
    [categories],
  );

  const withPct = distribution.map((d) => {
    const total = distribution.reduce((s, x) => s + x.count, 0) || 1;
    return { ...d, pct: ((d.count / total) * 100).toFixed(1) };
  });

  if (!categories.length && !distribution.length) {
    return (
      <div className="glass-panel rounded-2xl p-6 text-sm text-[var(--muted)]">
        Failure distribution will appear after backend classification and pattern detection complete.
      </div>
    );
  }

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <div className="glass-panel rounded-2xl p-4 lg:col-span-1">
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
          Fault Categories (Pie)
        </h3>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={categories} dataKey="count" nameKey="category" innerRadius={40} outerRadius={70}>
                {categories.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: "#111827", border: "1px solid rgba(255,255,255,0.1)" }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="glass-panel rounded-2xl p-4 lg:col-span-1">
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
          Failure Count (Bar)
        </h3>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={withPct.slice(0, 12)}>
              <CartesianGrid stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
              <XAxis dataKey="name" hide />
              <YAxis stroke="#94a3b8" fontSize={10} />
              <Tooltip
                formatter={(v, _n, p) => [`${v} (${(p.payload as { pct?: string }).pct}%)`, "Count"]}
                contentStyle={{ background: "#111827", border: "1px solid rgba(255,255,255,0.1)" }}
              />
              <Bar dataKey="count" fill="#38bdf8" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="glass-panel rounded-2xl p-4 lg:col-span-1">
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
          Category Treemap
        </h3>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <Treemap
              data={treemapData}
              dataKey="size"
              nameKey="name"
              stroke="#111827"
              fill="#7C3AED"
              animationDuration={800}
            />
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
});
