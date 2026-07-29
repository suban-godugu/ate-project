"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  AlertTriangle,
  Braces,
  Download,
  Gauge,
  Play,
  Search,
  TrendingUp,
} from "lucide-react";
import {
  computeFailureRates,
  FailureRateMetric,
  getFailureRateHistory,
  getFailureRateStatistics,
  getFailureRateTrends,
  listDatasets,
  listFailureRates,
  listPatterns,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import { FailureHeatmapCanvas } from "@/components/FailureHeatmapCanvas";
import { useAutoSelectFirstId } from "@/hooks/useAutoSelectFirstId";

const tooltipStyle = {
  background: "#111827",
  border: "1px solid rgba(255,255,255,.1)",
  borderRadius: 10,
};

export function FailureRateDashboard() {
  const qc = useQueryClient();
  const [datasetId, setDatasetId] = useState("");
  const [search, setSearch] = useState("");
  const [level, setLevel] = useState("pattern");
  const [selectedPattern, setSelectedPattern] = useState<string | null>(null);

  const datasets = useQuery({ queryKey: ["datasets"], queryFn: listDatasets });
  useAutoSelectFirstId(
    datasetId,
    setDatasetId,
    (datasets.data?.datasets || []).map((d) => d.id),
  );
  const metrics = useQuery({
    queryKey: ["failure-rates", level],
    queryFn: () => listFailureRates({ aggregation_level: level }),
    refetchInterval: 5000,
  });
  // The heatmap always needs wafer-level rows, independent of the table's level filter.
  const waferMetrics = useQuery({
    queryKey: ["failure-rates", "wafer"],
    queryFn: () => listFailureRates({ aggregation_level: "wafer" }),
    refetchInterval: 5000,
  });
  const stats = useQuery({
    queryKey: ["failure-rate-statistics"],
    queryFn: getFailureRateStatistics,
    refetchInterval: 5000,
  });
  const trends = useQuery({
    queryKey: ["failure-rate-trends"],
    queryFn: getFailureRateTrends,
    refetchInterval: 5000,
  });
  const history = useQuery({
    queryKey: ["failure-rate-history"],
    queryFn: getFailureRateHistory,
    refetchInterval: 5000,
  });
  const patterns = useQuery({ queryKey: ["patterns"], queryFn: () => listPatterns() });

  const compute = useMutation({
    mutationFn: () =>
      computeFailureRates({
        dataset_id: datasetId,
        async_execution: false,
        window_size: 5,
      }),
    onSuccess: async () => {
      await Promise.all([
        qc.invalidateQueries({ queryKey: ["failure-rates"] }),
        qc.invalidateQueries({ queryKey: ["failure-rate-statistics"] }),
        qc.invalidateQueries({ queryKey: ["failure-rate-trends"] }),
        qc.invalidateQueries({ queryKey: ["failure-rate-history"] }),
      ]);
    },
  });

  const rows = useMemo(() => {
    const all = metrics.data?.metrics || [];
    const filtered = search
      ? all.filter(
          (row) =>
            row.pattern_id.toLowerCase().includes(search.toLowerCase()) ||
            row.aggregation_key.toLowerCase().includes(search.toLowerCase()),
        )
      : all;
    return filtered;
  }, [metrics.data, search]);

  const chartRows = rows.slice(0, 12).map((row) => ({
    name: row.pattern_id.slice(0, 18),
    failure: Number(row.failure_percentage.toFixed(2)),
    baseline: Number((row.baseline_percentage ?? 0).toFixed(2)),
  }));
  const trendSeries = (trends.data?.trends || [])
    .filter((item) => item.aggregation_level === "pattern")
    .slice(0, 20)
    .map((item) => ({
      name: item.pattern_id.slice(0, 14),
      current: item.current_percentage,
      average: item.moving_average ?? item.current_percentage,
    }));
  const selectedRows = selectedPattern
    ? rows.filter((row) => row.pattern_id === selectedPattern)
    : rows.slice(0, 2);

  function exportJson() {
    const blob = new Blob(
      [JSON.stringify({ metrics: rows, trends: trends.data, history: history.data }, null, 2)],
      { type: "application/json" },
    );
    const link = document.createElement("a");
    link.download = `fa-fr-003-failure-rates-${new Date().toISOString()}.json`;
    link.href = URL.createObjectURL(blob);
    link.click();
    URL.revokeObjectURL(link.href);
  }

  function exportCsv() {
    const header = [
      "id",
      "pattern_id",
      "aggregation_level",
      "aggregation_key",
      "total_tests",
      "pass_count",
      "fail_count",
      "failure_percentage",
      "trend_status",
      "threshold_status",
      "severity_level",
    ];
    const lines = [
      header.join(","),
      ...rows.map((row) =>
        [
          row.id,
          row.pattern_id,
          row.aggregation_level,
          JSON.stringify(row.aggregation_key),
          row.total_tests,
          row.pass_count,
          row.fail_count,
          row.failure_percentage,
          row.trend_status,
          row.threshold_status,
          row.severity_level,
        ].join(","),
      ),
    ];
    const blob = new Blob([lines.join("\n")], { type: "text/csv" });
    const link = document.createElement("a");
    link.download = `fa-fr-003-failure-rates-${new Date().toISOString()}.csv`;
    link.href = URL.createObjectURL(blob);
    link.click();
    URL.revokeObjectURL(link.href);
  }

  return (
    <div className="space-y-5">
      <header className="glass-panel rounded-2xl p-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-xs font-semibold tracking-[0.2em] text-[var(--accent)]">
              FA-FR-003
            </p>
            <h1 className="mt-1 text-2xl font-semibold">Failure Rate Computation</h1>
            <p className="mt-2 max-w-3xl text-sm text-[var(--muted)]">
              Pattern-level failure percentages, density, trends, historical baselines, and
              threshold violations across device, die, wafer, lot, program, and batch scopes.
            </p>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={exportJson}
              className="rounded-xl border border-white/10 px-3 py-2 text-sm"
            >
              <Braces className="mr-2 inline" size={15} /> JSON
            </button>
            <button
              type="button"
              onClick={exportCsv}
              className="rounded-xl border border-white/10 px-3 py-2 text-sm"
            >
              <Download className="mr-2 inline" size={15} /> CSV
            </button>
          </div>
        </div>
      </header>

      <section className="glass-panel flex flex-wrap items-end gap-3 rounded-2xl p-4">
        <div className="min-w-72 flex-1">
          <label className="text-xs uppercase tracking-wide text-[var(--muted)]">
            Completed FA-FR-001 dataset with FA-FR-002 detection
          </label>
          <select
            value={datasetId}
            onChange={(event) => setDatasetId(event.target.value)}
            className="mt-1 block w-full rounded-xl border border-white/10 bg-[#111827] px-3 py-2 text-sm"
          >
            <option value="">Select dataset</option>
            {(datasets.data?.datasets || [])
              .filter((item: { status: string }) => item.status === "completed")
              .map((item: { id: string; name: string; records_accepted: number }) => (
                <option key={item.id} value={item.id}>
                  {item.name} · {item.records_accepted} records
                </option>
              ))}
          </select>
        </div>
        <button
          type="button"
          disabled={!datasetId || compute.isPending}
          onClick={() => compute.mutate()}
          className="rounded-xl bg-[var(--accent)] px-4 py-2 text-sm font-medium disabled:opacity-40"
        >
          <Play className="mr-2 inline" size={15} />
          {compute.isPending ? "Computing…" : "Run Computation"}
        </button>
        {compute.error && (
          <p className="max-w-xl text-xs text-red-300">
            {(compute.error as { response?: { data?: { detail?: unknown } } }).response?.data
              ?.detail
              ? JSON.stringify(
                  (compute.error as { response?: { data?: { detail?: unknown } } }).response
                    ?.data?.detail,
                )
              : compute.error.message}
          </p>
        )}
      </section>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard
          label="Persisted Metrics"
          value={stats.data?.total_metrics ?? 0}
          icon={Gauge}
        />
        <SummaryCard
          label="Average Failure %"
          value={`${Number(stats.data?.average_failure_percentage ?? 0).toFixed(2)}%`}
          icon={TrendingUp}
        />
        <SummaryCard
          label="Threshold Violations"
          value={stats.data?.threshold_violations ?? 0}
          icon={AlertTriangle}
        />
        <SummaryCard
          label="Detected Patterns Ready"
          value={patterns.data?.patterns?.length ?? 0}
          icon={Search}
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <ChartPanel title="Pattern Failure Summary">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartRows}>
              <CartesianGrid stroke="rgba(255,255,255,.05)" strokeDasharray="3 3" />
              <XAxis dataKey="name" hide />
              <YAxis stroke="#94a3b8" fontSize={10} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="failure" fill="#7c3aed" radius={[5, 5, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartPanel>
        <ChartPanel title="Historical Comparison">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartRows}>
              <CartesianGrid stroke="rgba(255,255,255,.05)" strokeDasharray="3 3" />
              <XAxis dataKey="name" hide />
              <YAxis stroke="#94a3b8" fontSize={10} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="baseline" fill="#38bdf8" radius={[5, 5, 0, 0]} />
              <Bar dataKey="failure" fill="#f87171" radius={[5, 5, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartPanel>
        <ChartPanel title="Failure Trend Charts">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={trendSeries}>
              <CartesianGrid stroke="rgba(255,255,255,.05)" strokeDasharray="3 3" />
              <XAxis dataKey="name" hide />
              <YAxis stroke="#94a3b8" fontSize={10} />
              <Tooltip contentStyle={tooltipStyle} />
              <Area dataKey="current" stroke="#7c3aed" fill="rgba(124,58,237,.25)" />
              <Area dataKey="average" stroke="#38bdf8" fill="rgba(56,189,248,.12)" />
            </AreaChart>
          </ResponsiveContainer>
        </ChartPanel>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.4fr_.8fr]">
        <section className="glass-panel overflow-hidden rounded-2xl">
          <div className="flex flex-wrap gap-2 border-b border-white/5 p-3">
            <div className="relative min-w-56 flex-1">
              <Search
                size={14}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)]"
              />
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search pattern or aggregation key"
                className="w-full rounded-lg border border-white/10 bg-black/25 py-2 pl-9 pr-3 text-sm"
              />
            </div>
            <select
              value={level}
              onChange={(event) => setLevel(event.target.value)}
              className="rounded-lg border border-white/10 bg-[#111827] px-3 text-sm"
            >
              {[
                "pattern",
                "device",
                "die",
                "wafer",
                "lot",
                "test_program",
                "batch",
              ].map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </div>
          <div className="max-h-[520px] overflow-auto">
            <table className="w-full text-left text-sm">
              <thead className="sticky top-0 bg-[#111827] text-[10px] uppercase text-[var(--muted)]">
                <tr>
                  <th className="px-3 py-2">Pattern</th>
                  <th className="px-3 py-2">Scope</th>
                  <th className="px-3 py-2">Fail %</th>
                  <th className="px-3 py-2">Trend</th>
                  <th className="px-3 py-2">Threshold</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr
                    key={row.id}
                    onClick={() => setSelectedPattern(row.pattern_id)}
                    className={cn(
                      "cursor-pointer border-t border-white/5 hover:bg-white/5",
                      selectedPattern === row.pattern_id && "bg-[var(--accent-soft)]",
                    )}
                  >
                    <td className="px-3 py-3">
                      <div className="font-medium">{row.pattern_id}</div>
                      <div className="text-[10px] text-[var(--muted)]">
                        {row.fail_count}/{row.total_tests}
                      </div>
                    </td>
                    <td className="px-3 py-3 text-[var(--muted)]">{row.aggregation_key}</td>
                    <td className="px-3 py-3">{row.failure_percentage.toFixed(2)}%</td>
                    <td className="px-3 py-3">
                      <Badge value={row.trend_status} />
                    </td>
                    <td className="px-3 py-3">
                      <Badge value={row.threshold_status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="space-y-4">
          <div className="glass-panel rounded-2xl p-4">
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
              Failure Heatmaps
            </h3>
            <FailureHeatmapCanvas
              metrics={waferMetrics.data?.metrics || metrics.data?.metrics || []}
            />
          </div>
          <div className="glass-panel rounded-2xl p-4">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
              Threshold Indicators
            </h3>
            <div className="space-y-2">
              {rows
                .filter((row) => row.threshold_status !== "within_limit")
                .slice(0, 6)
                .map((row) => (
                  <div
                    key={row.id}
                    className="rounded-lg border border-orange-400/20 bg-orange-500/10 px-3 py-2 text-sm"
                  >
                    <div className="font-medium">{row.pattern_id}</div>
                    <div className="text-xs text-orange-100">
                      {row.threshold_status} · {row.failure_percentage.toFixed(2)}% ·{" "}
                      {row.severity_level}
                    </div>
                  </div>
                ))}
              {!rows.some((row) => row.threshold_status !== "within_limit") && (
                <p className="text-sm text-[var(--muted)]">No threshold violations.</p>
              )}
            </div>
          </div>
        </section>
      </div>

      <PatternComparison rows={selectedRows} />

      <div className="grid gap-4 xl:grid-cols-2">
        <ChartPanel title="Historical Trend Analysis" tall>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={(history.data?.history || [])
                .slice()
                .reverse()
                .map(
                  (item: {
                    created_at?: string;
                    metric_count: number;
                    processing_ms: number;
                  }) => ({
                    time: item.created_at?.slice(5, 16).replace("T", " ") || "",
                    metrics: item.metric_count,
                    latency: item.processing_ms,
                  }),
                )}
            >
              <CartesianGrid stroke="rgba(255,255,255,.05)" strokeDasharray="3 3" />
              <XAxis dataKey="time" stroke="#94a3b8" fontSize={10} />
              <YAxis stroke="#94a3b8" fontSize={10} />
              <Tooltip contentStyle={tooltipStyle} />
              <Area dataKey="metrics" stroke="#7c3aed" fill="rgba(124,58,237,.25)" />
            </AreaChart>
          </ResponsiveContainer>
        </ChartPanel>
        <BenchmarkPanel stats={stats.data || {}} />
      </div>
    </div>
  );
}

function SummaryCard({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string | number;
  icon: React.ComponentType<{ size?: number; className?: string }>;
}) {
  return (
    <div className="glass-panel rounded-2xl p-4">
      <div className="flex justify-between text-xs uppercase text-[var(--muted)]">
        {label}
        <Icon size={15} className="text-[var(--accent)]" />
      </div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
    </div>
  );
}

function ChartPanel({
  title,
  children,
  tall = false,
}: {
  title: string;
  children: React.ReactNode;
  tall?: boolean;
}) {
  return (
    <section className="glass-panel rounded-2xl p-4">
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
        {title}
      </h3>
      <div className={tall ? "h-72" : "h-56"}>{children}</div>
    </section>
  );
}

function PatternComparison({ rows }: { rows: FailureRateMetric[] }) {
  return (
    <section className="glass-panel rounded-2xl p-4">
      <h3 className="mb-3 text-sm font-semibold uppercase text-[var(--muted)]">
        Pattern Comparison Charts
      </h3>
      <div className="grid gap-3 md:grid-cols-2">
        {rows.map((row) => (
          <div key={row.id} className="rounded-xl border border-white/5 bg-black/20 p-3">
            <div className="font-medium">{row.pattern_id}</div>
            <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-[var(--muted)]">
              <span>Failure %</span>
              <span>{row.failure_percentage.toFixed(2)}%</span>
              <span>Pass / Fail</span>
              <span>
                {row.pass_count} / {row.fail_count}
              </span>
              <span>Density</span>
              <span>{row.failure_density.toFixed(4)}</span>
              <span>Baseline Δ</span>
              <span>
                {row.historical_delta == null ? "n/a" : `${row.historical_delta.toFixed(2)}%`}
              </span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function BenchmarkPanel({ stats }: { stats: Record<string, unknown> }) {
  const latest = (stats.latest_benchmark_metrics || {}) as Record<string, number | null>;
  const metrics = [
    ["Computation Accuracy", latest.computation_accuracy],
    ["Throughput", latest.throughput_records_per_minute, " rec/min"],
    ["API / Processing", latest.api_processing_ms, " ms"],
    ["CPU Time", latest.cpu_time_ms, " ms"],
    ["Peak Memory", latest.peak_memory_mb, " MB"],
    ["DB Load", latest.database_load_ms, " ms"],
  ];
  return (
    <section className="glass-panel rounded-2xl p-4">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
        Benchmark Dashboard
      </h3>
      <div className="space-y-2">
        {metrics.map(([label, value, suffix]) => (
          <div
            key={String(label)}
            className="flex justify-between rounded-lg border border-white/5 bg-black/20 px-3 py-2 text-sm"
          >
            <span className="text-[var(--muted)]">{label}</span>
            <span>
              {value == null || value === undefined
                ? "Run a computation"
                : `${value}${suffix || ""}`}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}

function Badge({ value }: { value: string }) {
  return (
    <span
      className={cn(
        "rounded-full px-2 py-0.5 text-[10px] uppercase",
        value.includes("critical") && "bg-red-500/15 text-red-300",
        value.includes("warning") && "bg-orange-500/15 text-orange-300",
        value.includes("worsening") && "bg-red-500/15 text-red-300",
        value.includes("improving") && "bg-emerald-500/15 text-emerald-200",
        value.includes("stable") && "bg-sky-500/15 text-sky-200",
        value.includes("within") && "bg-emerald-500/15 text-emerald-200",
        value.includes("insufficient") && "bg-white/10 text-[var(--muted)]",
      )}
    >
      {value}
    </span>
  );
}
