"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  Braces,
  Download,
  GitCompareArrows,
  Play,
  Search,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
} from "lucide-react";
import {
  detectPatterns,
  DetectedPattern,
  getPattern,
  getPatternHistory,
  getPatternStatistics,
  listDatasets,
  listPatterns,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import { WaferCanvas } from "@/components/WaferCanvas";
import { useAutoSelectFirstId } from "@/hooks/useAutoSelectFirstId";

const COLORS = ["#7c3aed", "#38bdf8", "#34d399", "#fbbf24", "#f87171"];

export function PatternDashboard() {
  const qc = useQueryClient();
  const [datasetId, setDatasetId] = useState("");
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [severity, setSeverity] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const [compare, setCompare] = useState<string[]>([]);

  const datasets = useQuery({ queryKey: ["datasets"], queryFn: listDatasets });
  useAutoSelectFirstId(
    datasetId,
    setDatasetId,
    (datasets.data?.datasets || []).map((d) => d.id),
  );
  const patterns = useQuery({
    queryKey: ["patterns", search, category, severity],
    queryFn: () => listPatterns({ search, category, severity }),
    refetchInterval: 5000,
  });
  const stats = useQuery({
    queryKey: ["pattern-statistics"],
    queryFn: getPatternStatistics,
    refetchInterval: 5000,
  });
  const history = useQuery({
    queryKey: ["pattern-history"],
    queryFn: getPatternHistory,
    refetchInterval: 5000,
  });
  const detail = useQuery({
    queryKey: ["pattern-detail", selected],
    queryFn: () => getPattern(selected!),
    enabled: Boolean(selected),
  });

  const detect = useMutation({
    mutationFn: () =>
      detectPatterns({
        dataset_id: datasetId,
        async_execution: false,
        incremental: true,
      }),
    onSuccess: async () => {
      await Promise.all([
        qc.invalidateQueries({ queryKey: ["patterns"] }),
        qc.invalidateQueries({ queryKey: ["pattern-statistics"] }),
        qc.invalidateQueries({ queryKey: ["pattern-history"] }),
      ]);
    },
  });

  const rows = patterns.data?.patterns || [];
  useAutoSelectFirstId(
    selected || "",
    setSelected,
    rows.map((row) => row.id),
  );
  const categories = useMemo(
    () =>
      Object.entries(stats.data?.by_category || {}).map(([name, value]) => ({
        name,
        value,
      })),
    [stats.data],
  );
  const frequencies = rows.slice(0, 12).map((row) => ({
    name: row.pattern_name.slice(0, 18),
    frequency: Number((row.pattern_frequency * 100).toFixed(2)),
    occurrences: row.failure_count,
  }));
  const confidence = rows.slice(0, 12).map((row) => ({
    name: row.pattern_name.slice(0, 18),
    confidence: Number((row.confidence * 100).toFixed(1)),
  }));
  const timeline = (history.data?.history || [])
    .slice()
    .reverse()
    .map((item) => ({
      time: item.created_at?.slice(5, 16).replace("T", " ") || "",
      patterns: item.pattern_count,
      latency: item.processing_ms,
    }));
  const comparisonRows = rows.filter((row) => compare.includes(row.id));

  function exportJson() {
    const blob = new Blob([JSON.stringify({ patterns: rows, history: history.data }, null, 2)], {
      type: "application/json",
    });
    const link = document.createElement("a");
    link.download = `fa-fr-002-patterns-${new Date().toISOString()}.json`;
    link.href = URL.createObjectURL(blob);
    link.click();
    URL.revokeObjectURL(link.href);
  }

  function exportCsv() {
    const header = [
      "id",
      "pattern_id",
      "pattern_name",
      "pattern_category",
      "pattern_frequency",
      "confidence",
      "severity_level",
      "failure_count",
    ];
    const lines = [
      header.join(","),
      ...rows.map((row) =>
        [
          row.id,
          row.pattern_id,
          JSON.stringify(row.pattern_name),
          row.pattern_category,
          row.pattern_frequency,
          row.confidence,
          row.severity_level,
          row.failure_count,
        ].join(","),
      ),
    ];
    const blob = new Blob([lines.join("\n")], { type: "text/csv" });
    const link = document.createElement("a");
    link.download = `fa-fr-002-patterns-${new Date().toISOString()}.csv`;
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
              FA-FR-002
            </p>
            <h1 className="mt-1 text-2xl font-semibold">Failure Pattern Detection</h1>
            <p className="mt-2 max-w-3xl text-sm text-[var(--muted)]">
              Rule-based, recurring-signature, similarity-ready, and unknown-pattern detection
              across devices, dies, wafers, and lots.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
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
            Completed FA-FR-001 dataset
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
          disabled={!datasetId || detect.isPending}
          onClick={() => detect.mutate()}
          className="rounded-xl bg-[var(--accent)] px-4 py-2 text-sm font-medium disabled:opacity-40"
        >
          <Play className="mr-2 inline" size={15} />
          {detect.isPending ? "Detecting…" : "Run Detection"}
        </button>
        {detect.error && (
          <p className="max-w-lg text-xs text-red-300">
            {(detect.error as { response?: { data?: { detail?: unknown } } }).response?.data?.detail
              ? JSON.stringify(
                  (detect.error as { response?: { data?: { detail?: unknown } } }).response?.data
                    ?.detail,
                )
              : detect.error.message}
          </p>
        )}
      </section>

      <SummaryCards
        total={stats.data?.total_patterns || 0}
        confidence={stats.data?.average_confidence || 0}
        unknown={stats.data?.by_category?.unknown || 0}
        critical={stats.data?.by_severity?.critical || 0}
      />

      <div className="grid gap-4 xl:grid-cols-3">
        <ChartPanel title="Pattern Frequency">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={frequencies}>
              <CartesianGrid stroke="rgba(255,255,255,.05)" strokeDasharray="3 3" />
              <XAxis dataKey="name" hide />
              <YAxis stroke="#94a3b8" fontSize={10} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="frequency" fill="#7c3aed" radius={[5, 5, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartPanel>
        <ChartPanel title="Pattern Distribution">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={categories} dataKey="value" nameKey="name" innerRadius={48} outerRadius={82}>
                {categories.map((entry, index) => (
                  <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
        </ChartPanel>
        <ChartPanel title="Confidence Score">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={confidence} layout="vertical">
              <XAxis type="number" domain={[0, 100]} stroke="#94a3b8" fontSize={10} />
              <YAxis dataKey="name" type="category" hide />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="confidence" fill="#38bdf8" radius={[0, 5, 5, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartPanel>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.45fr_.75fr]">
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
                placeholder="Search patterns"
                className="w-full rounded-lg border border-white/10 bg-black/25 py-2 pl-9 pr-3 text-sm"
              />
            </div>
            <select
              value={category}
              onChange={(event) => setCategory(event.target.value)}
              className="rounded-lg border border-white/10 bg-[#111827] px-3 text-sm"
            >
              <option value="">All categories</option>
              {categories.map((item) => (
                <option key={item.name} value={item.name}>
                  {item.name}
                </option>
              ))}
            </select>
            <select
              value={severity}
              onChange={(event) => setSeverity(event.target.value)}
              className="rounded-lg border border-white/10 bg-[#111827] px-3 text-sm"
            >
              <option value="">All severities</option>
              {["critical", "high", "medium", "low"].map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </div>
          <div className="max-h-[520px] overflow-auto">
            <table className="w-full text-left text-sm">
              <thead className="sticky top-0 bg-[#111827] text-[10px] uppercase text-[var(--muted)]">
                <tr>
                  <th className="px-3 py-2">Compare</th>
                  <th className="px-3 py-2">Pattern</th>
                  <th className="px-3 py-2">Category</th>
                  <th className="px-3 py-2">Frequency</th>
                  <th className="px-3 py-2">Confidence</th>
                  <th className="px-3 py-2">Severity</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr
                    key={row.id}
                    onClick={() => setSelected(row.id)}
                    className={cn(
                      "cursor-pointer border-t border-white/5 hover:bg-white/5",
                      selected === row.id && "bg-[var(--accent-soft)]",
                    )}
                  >
                    <td className="px-3 py-3">
                      <input
                        type="checkbox"
                        checked={compare.includes(row.id)}
                        onClick={(event) => event.stopPropagation()}
                        onChange={() =>
                          setCompare((current) =>
                            current.includes(row.id)
                              ? current.filter((id) => id !== row.id)
                              : [...current.slice(-1), row.id],
                          )
                        }
                      />
                    </td>
                    <td className="px-3 py-3">
                      <div className="font-medium">{row.pattern_name}</div>
                      <div className="text-[10px] text-[var(--muted)]">{row.pattern_id}</div>
                    </td>
                    <td className="px-3 py-3 text-[var(--muted)]">{row.pattern_category}</td>
                    <td className="px-3 py-3">{(row.pattern_frequency * 100).toFixed(2)}%</td>
                    <td className="px-3 py-3">{(row.confidence * 100).toFixed(1)}%</td>
                    <td className="px-3 py-3">
                      <Severity value={row.severity_level} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="glass-panel rounded-2xl p-4">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
            Interactive Pattern Explorer
          </h3>
          {!detail.data ? (
            <p className="mt-4 text-sm text-[var(--muted)]">Select a pattern for evidence.</p>
          ) : (
            <div className="mt-3 space-y-4">
              <div>
                <div className="text-lg font-medium">{detail.data.pattern_name}</div>
                <div className="mt-1 text-xs text-[var(--muted)]">
                  {detail.data.detection_method} · {detail.data.occurrences.length} traceable
                  occurrences
                </div>
              </div>
              <WaferCanvas
                points={detail.data.occurrences.map((item: { x?: number; y?: number }) => ({
                  ...item,
                  severity: detail.data.severity_level,
                }))}
              />
              <div className="rounded-xl border border-violet-500/20 bg-violet-500/10 p-3">
                <div className="mb-1 text-xs font-semibold uppercase text-violet-200">
                  Engineering Notes
                </div>
                <p className="text-sm text-violet-100">
                  {detail.data.engineering_explanation || "No engineering note supplied."}
                </p>
              </div>
            </div>
          )}
        </section>
      </div>

      {comparisonRows.length > 0 && <Comparison rows={comparisonRows} />}

      <div className="grid gap-4 xl:grid-cols-[1.2fr_.8fr]">
        <ChartPanel title="Detection Timeline" tall>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={timeline}>
              <CartesianGrid stroke="rgba(255,255,255,.05)" strokeDasharray="3 3" />
              <XAxis dataKey="time" stroke="#94a3b8" fontSize={10} />
              <YAxis stroke="#94a3b8" fontSize={10} />
              <Tooltip contentStyle={tooltipStyle} />
              <Area dataKey="patterns" stroke="#7c3aed" fill="rgba(124,58,237,.25)" />
            </AreaChart>
          </ResponsiveContainer>
        </ChartPanel>
        <BenchmarkPanel history={history.data?.history || []} />
      </div>
    </div>
  );
}

function SummaryCards({
  total,
  confidence,
  unknown,
  critical,
}: {
  total: number;
  confidence: number;
  unknown: number;
  critical: number;
}) {
  const cards = [
    { label: "Detected Patterns", value: total, icon: Sparkles },
    { label: "Average Confidence", value: `${(confidence * 100).toFixed(1)}%`, icon: ShieldCheck },
    { label: "Unknown Review", value: unknown, icon: TriangleAlert },
    { label: "Critical Severity", value: critical, icon: TriangleAlert },
  ];
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map(({ label, value, icon: Icon }) => (
        <div key={label} className="glass-panel rounded-2xl p-4">
          <div className="flex justify-between text-xs uppercase text-[var(--muted)]">
            {label}
            <Icon size={15} className="text-[var(--accent)]" />
          </div>
          <div className="mt-2 text-2xl font-semibold">{value}</div>
        </div>
      ))}
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

function Comparison({ rows }: { rows: DetectedPattern[] }) {
  return (
    <section className="glass-panel rounded-2xl p-4">
      <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase text-[var(--muted)]">
        <GitCompareArrows size={16} /> Pattern Comparison
      </h3>
      <div className="grid gap-3 md:grid-cols-2">
        {rows.map((row) => (
          <div key={row.id} className="rounded-xl border border-white/5 bg-black/20 p-3">
            <div className="font-medium">{row.pattern_name}</div>
            <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-[var(--muted)]">
              <span>Confidence</span>
              <span>{(row.confidence * 100).toFixed(1)}%</span>
              <span>Occurrences</span>
              <span>{row.failure_count}</span>
              <span>Dies / Wafers / Lots</span>
              <span>
                {row.affected_die_count} / {row.affected_wafer_count} / {row.affected_lot_count}
              </span>
              <span>Method</span>
              <span>{row.detection_method}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function BenchmarkPanel({ history }: { history: Array<{ benchmark_metrics: Record<string, number | null> }> }) {
  const latest = history[0]?.benchmark_metrics || {};
  const metrics = [
    ["Precision", latest.precision],
    ["Recall", latest.recall],
    ["F1 Score", latest.f1_score],
    ["Latency", latest.detection_latency_ms, " ms"],
    ["Throughput", latest.throughput_records_per_minute, " rec/min"],
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
            <span>{value == null ? "Requires labeled ground truth" : `${value}${suffix || ""}`}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

function Severity({ value }: { value: string }) {
  return (
    <span
      className={cn(
        "rounded-full px-2 py-0.5 text-[10px] uppercase",
        value === "critical" && "bg-red-500/15 text-red-300",
        value === "high" && "bg-orange-500/15 text-orange-300",
        value === "medium" && "bg-amber-500/15 text-amber-200",
        value === "low" && "bg-emerald-500/15 text-emerald-200",
      )}
    >
      {value}
    </span>
  );
}

const tooltipStyle = {
  background: "#111827",
  border: "1px solid rgba(255,255,255,.1)",
  borderRadius: 10,
};
