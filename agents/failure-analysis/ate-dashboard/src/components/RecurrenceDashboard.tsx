"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  AlertTriangle,
  BrainCircuit,
  Braces,
  Download,
  Flame,
  Play,
  Repeat2,
  Search,
  ShieldCheck,
} from "lucide-react";
import {
  analyzeRecurrence,
  getRecurrenceHistory,
  getRecurrenceHotspots,
  getRecurrenceStatistics,
  getRecurrenceTrends,
  listUploads,
  listRecurrences,
  type RecurrenceMetric,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import { RecurrenceHotspotCanvas } from "@/components/RecurrenceHotspotCanvas";
import { useAutoSelectFirstId } from "@/hooks/useAutoSelectFirstId";
import { useAutoSelectFirstRow } from "@/hooks/useAutoSelectFirstRow";

const tooltipStyle = {
  background: "#111827",
  border: "1px solid rgba(255,255,255,.1)",
  borderRadius: 10,
};

export function RecurrenceDashboard() {
  const qc = useQueryClient();
  const [uploadId, setUploadId] = useState("");
  const [search, setSearch] = useState("");
  const [severity, setSeverity] = useState("");
  const [trend, setTrend] = useState("");
  const [historicalWindow, setHistoricalWindow] = useState(50);
  const [similarityThreshold, setSimilarityThreshold] = useState(0.72);
  const [selected, setSelected] = useState<RecurrenceMetric | null>(null);

  const uploads = useQuery({ queryKey: ["uploads"], queryFn: listUploads });
  useAutoSelectFirstId(
    uploadId,
    setUploadId,
    (uploads.data?.uploads || []).map((u) => u.id),
  );
  const recurrences = useQuery({
    queryKey: ["recurrences", severity, trend],
    queryFn: () =>
      listRecurrences({
        severity: severity || undefined,
        trend: trend || undefined,
      }),
    refetchInterval: 5000,
  });
  const trends = useQuery({
    queryKey: ["recurrence-trends"],
    queryFn: getRecurrenceTrends,
    refetchInterval: 5000,
  });
  const hotspots = useQuery({
    queryKey: ["recurrence-hotspots"],
    queryFn: getRecurrenceHotspots,
    refetchInterval: 5000,
  });
  const stats = useQuery({
    queryKey: ["recurrence-statistics"],
    queryFn: getRecurrenceStatistics,
    refetchInterval: 5000,
  });
  const history = useQuery({
    queryKey: ["recurrence-history"],
    queryFn: getRecurrenceHistory,
    refetchInterval: 5000,
  });

  const analyze = useMutation({
    mutationFn: () =>
      analyzeRecurrence({
        upload_id: uploadId,
        incremental: true,
        async_execution: false,
        historical_window: historicalWindow,
        similarity_threshold: similarityThreshold,
      }),
    onSuccess: async () => {
      await Promise.all([
        qc.invalidateQueries({ queryKey: ["recurrences"] }),
        qc.invalidateQueries({ queryKey: ["recurrence-trends"] }),
        qc.invalidateQueries({ queryKey: ["recurrence-hotspots"] }),
        qc.invalidateQueries({ queryKey: ["recurrence-statistics"] }),
        qc.invalidateQueries({ queryKey: ["recurrence-history"] }),
      ]);
    },
  });

  const rows = useMemo(() => {
    const items = recurrences.data?.recurrences || [];
    if (!search) return items;
    const query = search.toLowerCase();
    return items.filter(
      (item) =>
        item.pattern_id.toLowerCase().includes(query) ||
        item.pattern_name.toLowerCase().includes(query) ||
        item.fault_type.toLowerCase().includes(query) ||
        item.engineering_recommendation.toLowerCase().includes(query),
    );
  }, [recurrences.data, search]);

  useAutoSelectFirstRow(selected, setSelected, rows);

  const selectedTrend = (trends.data?.trends || []).find(
    (item) => item.recurrence_id === selected?.recurrence_id,
  );
  const frequencyRows = rows.slice(0, 15).map((item) => ({
    pattern: item.pattern_id.slice(0, 16),
    current: Number(item.recurrence_percentage.toFixed(3)),
    historical: Number((item.historical_frequency * 100).toFixed(3)),
  }));
  const confidenceRows = rows.slice(0, 15).map((item) => ({
    pattern: item.pattern_id.slice(0, 16),
    confidence: Number((item.confidence_score * 100).toFixed(1)),
    count: item.recurrence_count,
  }));
  const timelineRows = (selectedTrend?.time_series || []).map((item, index) => ({
    execution: `${index + 1}`,
    frequency: Number((item.frequency * 100).toFixed(3)),
    current: item.is_current ? Number((item.frequency * 100).toFixed(3)) : null,
  }));

  function exportJson() {
    download(
      JSON.stringify(
        {
          recurrences: rows,
          trends: trends.data?.trends || [],
          hotspots: hotspots.data?.hotspots || [],
          history: history.data?.history || [],
        },
        null,
        2,
      ),
      `fa-fr-004-recurrence-${new Date().toISOString()}.json`,
      "application/json",
    );
  }

  function exportCsv() {
    const header = [
      "recurrence_id",
      "pattern_id",
      "fault_type",
      "recurrence_count",
      "recurrence_frequency",
      "confidence_score",
      "severity",
      "trend_direction",
      "first_occurrence",
      "latest_occurrence",
      "historical_frequency",
      "engineering_recommendation",
    ];
    const lines = [
      header.join(","),
      ...rows.map((item) =>
        [
          item.recurrence_id,
          item.pattern_id,
          item.fault_type,
          item.recurrence_count,
          item.recurrence_frequency,
          item.confidence_score,
          item.severity,
          item.trend_direction,
          item.first_occurrence,
          item.latest_occurrence,
          item.historical_frequency,
          JSON.stringify(item.engineering_recommendation),
        ].join(","),
      ),
    ];
    download(
      lines.join("\n"),
      `fa-fr-004-recurrence-${new Date().toISOString()}.csv`,
      "text/csv",
    );
  }

  return (
    <div className="space-y-5">
      <header className="glass-panel rounded-2xl p-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-xs font-semibold tracking-[0.2em] text-[var(--accent)]">
              FA-FR-005
            </p>
            <h1 className="mt-1 text-2xl font-semibold">Recurring Failure Identification</h1>
            <p className="mt-2 max-w-3xl text-sm text-[var(--muted)]">
              Cross-execution pattern and classified-fault recurrence, historical comparison,
              similarity grouping, wafer hotspots, and actionable engineering recommendations.
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

      <section className="glass-panel grid gap-3 rounded-2xl p-4 xl:grid-cols-[1fr_160px_180px_auto]">
        <label className="text-xs uppercase tracking-wide text-[var(--muted)]">
          Completed FA-FR-001 → 004 upload
          <select
            value={uploadId}
            onChange={(event) => setUploadId(event.target.value)}
            className="mt-1 block w-full rounded-xl border border-white/10 bg-[#111827] px-3 py-2 text-sm normal-case text-white"
          >
            <option value="">Select upload</option>
            {(uploads.data?.uploads || [])
              .filter((item) => item.status === "completed")
              .map((item) => (
                <option key={item.id} value={item.id}>
                  {item.original_filename} · {item.records_accepted || 0} records
                </option>
              ))}
          </select>
        </label>
        <label className="text-xs uppercase tracking-wide text-[var(--muted)]">
          Historical window
          <input
            type="number"
            min={2}
            max={500}
            value={historicalWindow}
            onChange={(event) => setHistoricalWindow(Number(event.target.value))}
            className="mt-1 block w-full rounded-xl border border-white/10 bg-black/25 px-3 py-2 text-sm text-white"
          />
        </label>
        <label className="text-xs uppercase tracking-wide text-[var(--muted)]">
          Similarity threshold
          <input
            type="number"
            min={0}
            max={1}
            step={0.01}
            value={similarityThreshold}
            onChange={(event) => setSimilarityThreshold(Number(event.target.value))}
            className="mt-1 block w-full rounded-xl border border-white/10 bg-black/25 px-3 py-2 text-sm text-white"
          />
        </label>
        <button
          type="button"
          disabled={!uploadId || analyze.isPending}
          onClick={() => analyze.mutate()}
          className="self-end rounded-xl bg-[var(--accent)] px-4 py-2 text-sm font-medium disabled:opacity-40"
        >
          <Play className="mr-2 inline" size={15} />
          {analyze.isPending ? "Analyzing…" : "Run Recurrence Analysis"}
        </button>
        {analyze.error && (
          <p className="text-xs text-red-300 xl:col-span-4">
            {apiError(analyze.error)}
          </p>
        )}
      </section>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard
          label="Recurring Signatures"
          value={stats.data?.total_recurrences ?? 0}
          icon={Repeat2}
        />
        <SummaryCard
          label="Average Confidence"
          value={`${Number((stats.data?.average_confidence ?? 0) * 100).toFixed(1)}%`}
          icon={ShieldCheck}
        />
        <SummaryCard
          label="Spatial Hotspots"
          value={stats.data?.hotspot_count ?? 0}
          icon={Flame}
        />
        <SummaryCard
          label="Critical Patterns"
          value={stats.data?.critical_count ?? 0}
          icon={AlertTriangle}
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <ChartPanel title="Pattern Frequency">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={frequencyRows}>
              <CartesianGrid stroke="rgba(255,255,255,.05)" strokeDasharray="3 3" />
              <XAxis dataKey="pattern" hide />
              <YAxis stroke="#94a3b8" fontSize={10} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="current" fill="#7c3aed" radius={[5, 5, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartPanel>
        <ChartPanel title="Historical Comparison">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={frequencyRows}>
              <CartesianGrid stroke="rgba(255,255,255,.05)" strokeDasharray="3 3" />
              <XAxis dataKey="pattern" hide />
              <YAxis stroke="#94a3b8" fontSize={10} />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend />
              <Bar dataKey="historical" fill="#38bdf8" radius={[5, 5, 0, 0]} />
              <Bar dataKey="current" fill="#f97316" radius={[5, 5, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartPanel>
        <ChartPanel title="Confidence Score Dashboard">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={confidenceRows}>
              <CartesianGrid stroke="rgba(255,255,255,.05)" strokeDasharray="3 3" />
              <XAxis dataKey="pattern" hide />
              <YAxis domain={[0, 100]} stroke="#94a3b8" fontSize={10} />
              <Tooltip contentStyle={tooltipStyle} />
              <Area
                dataKey="confidence"
                stroke="#34d399"
                fill="rgba(52,211,153,.2)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </ChartPanel>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.4fr_.8fr]">
        <section className="glass-panel overflow-hidden rounded-2xl">
          <div className="flex flex-wrap gap-2 border-b border-white/5 p-3">
            <div className="relative min-w-60 flex-1">
              <Search
                size={14}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)]"
              />
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search pattern, fault type, or recommendation"
                className="w-full rounded-lg border border-white/10 bg-black/25 py-2 pl-9 pr-3 text-sm"
              />
            </div>
            <select
              value={severity}
              onChange={(event) => setSeverity(event.target.value)}
              className="rounded-lg border border-white/10 bg-[#111827] px-3 text-sm"
            >
              <option value="">All severity</option>
              {["critical", "high", "medium", "low"].map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
            <select
              value={trend}
              onChange={(event) => setTrend(event.target.value)}
              className="rounded-lg border border-white/10 bg-[#111827] px-3 text-sm"
            >
              <option value="">All trends</option>
              {["emerging", "increasing", "stable", "decreasing"].map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </div>
          <div className="max-h-[560px] overflow-auto">
            <table className="w-full text-left text-sm">
              <thead className="sticky top-0 bg-[#111827] text-[10px] uppercase text-[var(--muted)]">
                <tr>
                  <th className="px-3 py-2">Pattern</th>
                  <th className="px-3 py-2">Fault Type</th>
                  <th className="px-3 py-2">Count</th>
                  <th className="px-3 py-2">Frequency</th>
                  <th className="px-3 py-2">Confidence</th>
                  <th className="px-3 py-2">Trend</th>
                  <th className="px-3 py-2">Severity</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((item) => (
                  <tr
                    key={item.recurrence_id}
                    onClick={() => setSelected(item)}
                    className={cn(
                      "cursor-pointer border-t border-white/5 hover:bg-white/5",
                      selected?.recurrence_id === item.recurrence_id &&
                        "bg-[var(--accent-soft)]",
                    )}
                  >
                    <td className="px-3 py-3">
                      <div className="font-medium">{item.pattern_id}</div>
                      <div className="text-[10px] text-[var(--muted)]">
                        {item.pattern_name}
                      </div>
                    </td>
                    <td className="px-3 py-3 text-[var(--muted)]">{item.fault_type}</td>
                    <td className="px-3 py-3">{item.recurrence_count}</td>
                    <td className="px-3 py-3">
                      {item.recurrence_percentage.toFixed(3)}%
                    </td>
                    <td className="px-3 py-3">
                      {(item.confidence_score * 100).toFixed(1)}%
                    </td>
                    <td className="px-3 py-3">
                      <Badge value={item.trend_direction} />
                    </td>
                    <td className="px-3 py-3">
                      <Badge value={item.severity} />
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
              Hotspot Heatmap · Wafer Overlay
            </h3>
            <RecurrenceHotspotCanvas
              hotspots={hotspots.data?.hotspots || []}
              selectedPattern={selected?.pattern_id}
            />
          </div>
          <div className="glass-panel rounded-2xl p-4">
            <h3 className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
              <BrainCircuit size={15} /> Engineering Recommendation
            </h3>
            {selected ? (
              <>
                <div className="mb-2 flex items-center gap-2">
                  <span className="font-medium">{selected.pattern_id}</span>
                  <Badge value={selected.severity} />
                </div>
                <p className="text-sm leading-6 text-slate-200">
                  {selected.engineering_recommendation}
                </p>
                <p className="mt-3 text-xs text-[var(--muted)]">
                  Similarity group: {selected.similarity_group || "n/a"} · First seen{" "}
                  {new Date(selected.first_occurrence).toLocaleString()}
                </p>
              </>
            ) : (
              <p className="text-sm text-[var(--muted)]">
                Select a recurring pattern to review its explainable recommendation.
              </p>
            )}
          </div>
        </section>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <ChartPanel title="Pattern Timeline" tall>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={timelineRows}>
              <CartesianGrid stroke="rgba(255,255,255,.05)" strokeDasharray="3 3" />
              <XAxis dataKey="execution" stroke="#94a3b8" fontSize={10} />
              <YAxis stroke="#94a3b8" fontSize={10} />
              <Tooltip contentStyle={tooltipStyle} />
              <Line dataKey="frequency" stroke="#7c3aed" strokeWidth={2} />
              <Line dataKey="current" stroke="#f97316" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </ChartPanel>
        <ChartPanel title="Recurrence Trend Charts" tall>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={(history.data?.history || [])
                .slice()
                .reverse()
                .map(
                  (item: {
                    created_at?: string;
                    recurrence_count: number;
                    processing_ms: number;
                  }) => ({
                    time: item.created_at?.slice(5, 16).replace("T", " ") || "",
                    recurrences: item.recurrence_count,
                    latency: item.processing_ms,
                  }),
                )}
            >
              <CartesianGrid stroke="rgba(255,255,255,.05)" strokeDasharray="3 3" />
              <XAxis dataKey="time" stroke="#94a3b8" fontSize={10} />
              <YAxis stroke="#94a3b8" fontSize={10} />
              <Tooltip contentStyle={tooltipStyle} />
              <Area
                dataKey="recurrences"
                stroke="#7c3aed"
                fill="rgba(124,58,237,.25)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </ChartPanel>
      </div>

      <BenchmarkPanel stats={stats.data || {}} />
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

function BenchmarkPanel({ stats }: { stats: Record<string, unknown> }) {
  const latest = (stats.latest_benchmark_metrics || {}) as Record<
    string,
    number | boolean | null
  >;
  const metrics = [
    ["Precision", latest.precision],
    ["Recall", latest.recall],
    ["F1 Score", latest.f1_score],
    ["False Positive Rate", latest.false_positive_rate],
    ["False Negative Rate", latest.false_negative_rate],
    ["Detection Latency", latest.detection_latency_ms, " ms"],
    ["Throughput", latest.throughput_records_per_second, " obs/s"],
    ["Process Memory", latest.process_memory_mb, " MB"],
  ];
  return (
    <section className="glass-panel rounded-2xl p-4">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
        Evaluation Benchmark Metrics
      </h3>
      <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map(([label, value, suffix]) => (
          <div
            key={String(label)}
            className="rounded-lg border border-white/5 bg-black/20 px-3 py-2 text-sm"
          >
            <div className="text-xs text-[var(--muted)]">{label}</div>
            <div className="mt-1 font-medium">
              {value == null || value === undefined
                ? "Ground truth required"
                : `${value}${suffix || ""}`}
            </div>
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
        ["critical", "increasing", "emerging"].includes(value) &&
          "bg-red-500/15 text-red-300",
        value === "high" && "bg-orange-500/15 text-orange-300",
        ["decreasing", "low"].includes(value) && "bg-emerald-500/15 text-emerald-200",
        ["stable", "medium"].includes(value) && "bg-sky-500/15 text-sky-200",
      )}
    >
      {value}
    </span>
  );
}

function download(content: string, filename: string, type: string) {
  const blob = new Blob([content], { type });
  const link = document.createElement("a");
  link.download = filename;
  link.href = URL.createObjectURL(blob);
  link.click();
  URL.revokeObjectURL(link.href);
}

function apiError(error: Error): string {
  const detail = (
    error as {
      response?: { data?: { detail?: unknown } };
    }
  ).response?.data?.detail;
  return detail ? JSON.stringify(detail) : error.message;
}
