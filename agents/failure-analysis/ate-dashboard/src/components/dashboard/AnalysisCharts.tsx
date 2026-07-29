"use client";

import { memo } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import type { DashboardCharts } from "@/stores/analysisStore";

const COLORS = ["#7C3AED", "#38bdf8", "#f472b6", "#34d399", "#fbbf24", "#fb7185"];

type Props = {
  charts: DashboardCharts | null;
  loading?: boolean;
};

function ChartShell({
  title,
  children,
  empty,
}: {
  title: string;
  children: React.ReactNode;
  empty?: boolean;
}) {
  return (
    <div className="glass-panel rounded-2xl p-4">
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
        {title}
      </h3>
      {empty ? (
        <p className="flex h-52 items-center justify-center text-sm text-[var(--muted)]">
          No backend data for this chart yet.
        </p>
      ) : (
        <div className="h-52">{children}</div>
      )}
    </div>
  );
}

function ChartSkeleton({ title }: { title: string }) {
  return (
    <div className="glass-panel rounded-2xl p-4">
      <div className="mb-3 h-4 w-32 animate-pulse rounded bg-white/10" />
      <div className="h-52 animate-pulse rounded-xl bg-white/5" />
      <span className="sr-only">{title}</span>
    </div>
  );
}

export const AnalysisCharts = memo(function AnalysisCharts({ charts, loading }: Props) {
  if (loading) {
    return (
      <div className="grid gap-4 lg:grid-cols-2">
        {[
          "Failure Trend",
          "Failure Distribution",
          "Category Distribution",
          "Pass vs Fail",
          "Wafer Heatmap",
          "Die Heatmap",
        ].map((t) => (
          <ChartSkeleton key={t} title={t} />
        ))}
      </div>
    );
  }

  if (!charts) return null;

  const trend = charts.failure_trend;
  const distribution = charts.failure_distribution;
  const categories = charts.category_distribution.filter((row) => row.count > 0);
  const passFail = charts.pass_vs_fail;
  const wafer = charts.wafer_heatmap;
  const die = charts.die_heatmap;
  const corrNodes = Array.isArray(charts.correlation_graph?.nodes)
    ? (charts.correlation_graph.nodes as Array<{ label?: string; weight?: number }>)
    : Array.isArray(charts.correlation_graph?.correlations)
      ? (charts.correlation_graph.correlations as Array<{
          pattern_id?: string;
          correlation_coefficient?: number;
        }>).map((c) => ({
          label: c.pattern_id,
          weight: c.correlation_coefficient,
        }))
      : [];

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <ChartShell title="Failure Trend" empty={!trend.length}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={trend}>
            <defs>
              <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#7C3AED" stopOpacity={0.45} />
                <stop offset="100%" stopColor="#7C3AED" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
            <XAxis dataKey="label" stroke="#94a3b8" fontSize={10} tick={{ fill: "#94a3b8" }} />
            <YAxis stroke="#94a3b8" fontSize={10} tick={{ fill: "#94a3b8" }} />
            <Tooltip
              contentStyle={{
                background: "#111827",
                border: "1px solid rgba(255,255,255,0.1)",
              }}
            />
            <Area
              type="monotone"
              dataKey="rate"
              stroke="#7C3AED"
              fill="url(#trendFill)"
              animationDuration={800}
            />
          </AreaChart>
        </ResponsiveContainer>
      </ChartShell>

      <ChartShell title="Failure Distribution" empty={!distribution.length}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={distribution}>
            <CartesianGrid stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
            <XAxis dataKey="name" stroke="#94a3b8" fontSize={10} hide />
            <YAxis stroke="#94a3b8" fontSize={10} />
            <Tooltip
              contentStyle={{
                background: "#111827",
                border: "1px solid rgba(255,255,255,0.1)",
              }}
            />
            <Bar dataKey="count" fill="#38bdf8" radius={[4, 4, 0, 0]} animationDuration={800} />
          </BarChart>
        </ResponsiveContainer>
      </ChartShell>

      <ChartShell title="Category Distribution" empty={!categories.length}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={categories}>
            <CartesianGrid stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
            <XAxis dataKey="category" stroke="#94a3b8" fontSize={10} />
            <YAxis stroke="#94a3b8" fontSize={10} />
            <Tooltip
              contentStyle={{
                background: "#111827",
                border: "1px solid rgba(255,255,255,0.1)",
              }}
            />
            <Bar dataKey="count" fill="#f472b6" radius={[4, 4, 0, 0]} animationDuration={800} />
          </BarChart>
        </ResponsiveContainer>
      </ChartShell>

      <ChartShell title="Pass vs Fail" empty={!passFail.length}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={passFail}
              dataKey="value"
              nameKey="name"
              innerRadius={45}
              outerRadius={70}
              paddingAngle={3}
              animationDuration={800}
            >
              {passFail.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Legend />
            <Tooltip
              contentStyle={{
                background: "#111827",
                border: "1px solid rgba(255,255,255,0.1)",
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </ChartShell>

      <ChartShell title="Wafer Heatmap" empty={!wafer.length}>
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart>
            <CartesianGrid stroke="rgba(255,255,255,0.06)" />
            <XAxis type="number" dataKey="x" stroke="#94a3b8" fontSize={10} />
            <YAxis type="number" dataKey="y" stroke="#94a3b8" fontSize={10} />
            <ZAxis type="number" dataKey="intensity" range={[40, 400]} />
            <Tooltip
              cursor={{ strokeDasharray: "3 3" }}
              contentStyle={{
                background: "#111827",
                border: "1px solid rgba(255,255,255,0.1)",
              }}
            />
            <Scatter data={wafer} fill="#34d399" animationDuration={800} />
          </ScatterChart>
        </ResponsiveContainer>
      </ChartShell>

      <ChartShell title="Die Heatmap" empty={!die.length}>
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart>
            <CartesianGrid stroke="rgba(255,255,255,0.06)" />
            <XAxis type="number" dataKey="x" stroke="#94a3b8" fontSize={10} />
            <YAxis type="number" dataKey="y" stroke="#94a3b8" fontSize={10} />
            <ZAxis type="number" dataKey="intensity" range={[40, 400]} />
            <Tooltip
              cursor={{ strokeDasharray: "3 3" }}
              contentStyle={{
                background: "#111827",
                border: "1px solid rgba(255,255,255,0.1)",
              }}
            />
            <Scatter data={die} fill="#fbbf24" animationDuration={800} />
          </ScatterChart>
        </ResponsiveContainer>
      </ChartShell>

      <ChartShell title="Correlation Graph" empty={!corrNodes.length} >
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={corrNodes.slice(0, 16).map((n) => ({
              name: n.label || "—",
              weight: Number(n.weight || 0),
            }))}
            layout="vertical"
          >
            <CartesianGrid stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
            <XAxis type="number" stroke="#94a3b8" fontSize={10} />
            <YAxis type="category" dataKey="name" width={80} stroke="#94a3b8" fontSize={9} />
            <Tooltip
              contentStyle={{
                background: "#111827",
                border: "1px solid rgba(255,255,255,0.1)",
              }}
            />
            <Bar dataKey="weight" fill="#fb7185" radius={[0, 4, 4, 0]} animationDuration={800} />
          </BarChart>
        </ResponsiveContainer>
      </ChartShell>
    </div>
  );
});
