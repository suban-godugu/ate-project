"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  Activity,
  Braces,
  Cpu,
  Download,
  Flame,
  Grid3x3,
  HeartPulse,
  Play,
  Search,
  ShieldCheck,
  Target,
} from "lucide-react";
import {
  analyzeDieLevel,
  getDieClusters,
  getDieDetail,
  getDieHotspots,
  getDieStatistics,
  listDieAnalyses,
  listUploads,
  type DieSummary,
} from "@/lib/api";
import { DieMapCanvas } from "@/components/DieMapCanvas";
import { cn } from "@/lib/utils";
import { useAutoSelectFirstId } from "@/hooks/useAutoSelectFirstId";
import { useAutoSelectFirstRow } from "@/hooks/useAutoSelectFirstRow";

const tooltipStyle = {
  background: "#111827",
  border: "1px solid rgba(255,255,255,.1)",
  borderRadius: 10,
};

export function DieAnalysisDashboard() {
  const qc = useQueryClient();
  const [uploadId, setUploadId] = useState("");
  const [search, setSearch] = useState("");
  const [severity, setSeverity] = useState("");
  const [failingOnly, setFailingOnly] = useState(false);
  const [historicalWindow, setHistoricalWindow] = useState(50);
  const [hotspotThreshold, setHotspotThreshold] = useState(0.05);
  const [clusterEps, setClusterEps] = useState(1.5);
  const [confidence, setConfidence] = useState(0.55);
  const [mapMode, setMapMode] = useState<"wafer" | "heatmap" | "clusters">("wafer");
  const [selected, setSelected] = useState<DieSummary | null>(null);

  const uploads = useQuery({ queryKey: ["uploads"], queryFn: listUploads });
  useAutoSelectFirstId(
    uploadId,
    setUploadId,
    (uploads.data?.uploads || []).map((u) => u.id),
  );
  const diesQuery = useQuery({
    queryKey: ["die-analyses", severity, failingOnly],
    queryFn: () =>
      listDieAnalyses({
        severity: severity || undefined,
        is_failing: failingOnly ? true : undefined,
      }),
    refetchInterval: 5000,
  });
  const hotspots = useQuery({
    queryKey: ["die-hotspots"],
    queryFn: () => getDieHotspots(),
    refetchInterval: 5000,
  });
  const clusters = useQuery({
    queryKey: ["die-clusters"],
    queryFn: () => getDieClusters(),
    refetchInterval: 5000,
  });
  const stats = useQuery({
    queryKey: ["die-statistics"],
    queryFn: getDieStatistics,
    refetchInterval: 5000,
  });
  const detail = useQuery({
    queryKey: ["die-detail", selected?.die_result_id],
    queryFn: () => getDieDetail(selected!.die_result_id),
    enabled: Boolean(selected?.die_result_id),
  });

  const analyze = useMutation({
    mutationFn: () =>
      analyzeDieLevel({
        upload_id: uploadId,
        historical_window: historicalWindow,
        hotspot_density_threshold: hotspotThreshold,
        cluster_eps: clusterEps,
        confidence_threshold: confidence,
        incremental: true,
        async_execution: false,
      }),
    onSuccess: async () =>
      Promise.all([
        qc.invalidateQueries({ queryKey: ["die-analyses"] }),
        qc.invalidateQueries({ queryKey: ["die-hotspots"] }),
        qc.invalidateQueries({ queryKey: ["die-clusters"] }),
        qc.invalidateQueries({ queryKey: ["die-statistics"] }),
        qc.invalidateQueries({ queryKey: ["die-detail"] }),
      ]),
  });

  const rows = useMemo(() => {
    const values = (diesQuery.data?.dies || []).map((die, index) => {
      if (typeof die.x === "number" && typeof die.y === "number") return die;
      const ring = Math.floor(Math.sqrt(index + 1));
      const angle = (index * 2.399963) % (Math.PI * 2);
      return {
        ...die,
        x: Math.round(Math.cos(angle) * (ring + 1) * 10),
        y: Math.round(Math.sin(angle) * (ring + 1) * 10),
      };
    });
    const query = search.toLowerCase();
    return query
      ? values.filter((row) =>
          `${row.lot_id} ${row.wafer_id} ${row.die_id} ${row.dominant_pattern_id} ${row.dominant_fault_type} ${row.engineering_recommendation}`
            .toLowerCase()
            .includes(query),
        )
      : values;
  }, [diesQuery.data, search]);

  useAutoSelectFirstRow(selected, setSelected, rows);

  const densityData = rows.slice(0, 24).map((row) => ({
    die: row.die_id.slice(0, 10),
    density: Number((row.failure_density * 100).toFixed(2)),
    neighbors: row.neighbor_failure_count,
  }));
  const healthData = rows.slice(0, 24).map((row) => ({
    die: row.die_id.slice(0, 10),
    health: Number((row.health_score * 100).toFixed(2)),
    confidence: Number((row.confidence_score * 100).toFixed(2)),
  }));
  const trendBuckets = useMemo(() => {
    const buckets: Record<string, number> = {
      increasing: 0,
      decreasing: 0,
      stable: 0,
      unknown: 0,
    };
    rows.forEach((row) => {
      const key = row.trend_status in buckets ? row.trend_status : "unknown";
      buckets[key] += 1;
    });
    return Object.entries(buckets).map(([trend, count]) => ({ trend, count }));
  }, [rows]);

  const benchmarks = stats.data?.benchmark_metrics || {};

  function exportData(format: "json" | "csv") {
    const payload = {
      dies: rows,
      hotspots: hotspots.data?.hotspots || [],
      clusters: clusters.data?.clusters || [],
      statistics: stats.data || {},
      selected_detail: detail.data || null,
    };
    const content =
      format === "json"
        ? JSON.stringify(payload, null, 2)
        : [
            "die_result_id,lot_id,wafer_id,die_id,failure_density,health_score,confidence,severity,trend,isolated,hotspot_id,cluster_id,recommendation",
            ...rows.map((row) =>
              [
                row.die_result_id,
                row.lot_id,
                row.wafer_id,
                row.die_id,
                row.failure_density,
                row.health_score,
                row.confidence_score,
                row.severity,
                row.trend_status,
                row.is_isolated,
                row.hotspot_id,
                row.cluster_id,
                JSON.stringify(row.engineering_recommendation),
              ].join(","),
            ),
          ].join("\n");
    const link = document.createElement("a");
    link.href = URL.createObjectURL(
      new Blob([content], { type: format === "json" ? "application/json" : "text/csv" }),
    );
    link.download = `fa-fr-007-die-analysis-${new Date().toISOString()}.${format}`;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  return (
    <div className="space-y-5">
      <header className="glass-panel rounded-2xl p-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-xs font-semibold tracking-[.2em] text-[var(--accent)]">
              FA-FR-007
            </p>
            <h1 className="mt-1 text-2xl font-semibold">Die-Level Failure Analysis</h1>
            <p className="mt-2 max-w-3xl text-sm text-[var(--muted)]">
              Per-die density, neighbor isolation, hotspot membership, cluster membership,
              health scoring, trends, and actionable engineering recommendations with full
              FA-FR-001 → 006 lineage.
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => exportData("json")}
              className="rounded-xl border border-white/10 px-3 py-2 text-sm"
            >
              <Braces className="mr-2 inline" size={15} />
              JSON
            </button>
            <button
              onClick={() => exportData("csv")}
              className="rounded-xl border border-white/10 px-3 py-2 text-sm"
            >
              <Download className="mr-2 inline" size={15} />
              CSV
            </button>
          </div>
        </div>
      </header>

      <section className="glass-panel grid gap-3 rounded-2xl p-4 xl:grid-cols-[1fr_110px_120px_110px_110px_auto]">
        <Field label="Completed FA-FR-001 → 006 upload">
          <select
            value={uploadId}
            onChange={(e) => setUploadId(e.target.value)}
            className="input"
          >
            <option value="">Select upload</option>
            {(uploads.data?.uploads || [])
              .filter((row) => row.status === "completed")
              .map((row) => (
                <option key={row.id} value={row.id}>
                  {row.original_filename}
                </option>
              ))}
          </select>
        </Field>
        <Field label="History">
          <input
            className="input"
            type="number"
            min={2}
            max={500}
            value={historicalWindow}
            onChange={(e) => setHistoricalWindow(Number(e.target.value))}
          />
        </Field>
        <Field label="Hotspot dens.">
          <input
            className="input"
            type="number"
            min={0}
            max={1}
            step={0.01}
            value={hotspotThreshold}
            onChange={(e) => setHotspotThreshold(Number(e.target.value))}
          />
        </Field>
        <Field label="Cluster eps">
          <input
            className="input"
            type="number"
            min={0.1}
            max={100}
            step={0.1}
            value={clusterEps}
            onChange={(e) => setClusterEps(Number(e.target.value))}
          />
        </Field>
        <Field label="Confidence">
          <input
            className="input"
            type="number"
            min={0}
            max={1}
            step={0.01}
            value={confidence}
            onChange={(e) => setConfidence(Number(e.target.value))}
          />
        </Field>
        <button
          disabled={!uploadId || analyze.isPending}
          onClick={() => analyze.mutate()}
          className="self-end rounded-xl bg-[var(--accent)] px-4 py-2 text-sm font-medium disabled:opacity-40"
        >
          <Play className="mr-2 inline" size={15} />
          {analyze.isPending ? "Analyzing…" : "Run Die Analysis"}
        </button>
        {analyze.error && (
          <p className="text-xs text-red-300 xl:col-span-6">{String(analyze.error)}</p>
        )}
      </section>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Card label="Total Dies" value={stats.data?.total_dies ?? 0} icon={Grid3x3} />
        <Card label="Failing Dies" value={stats.data?.failing_dies ?? 0} icon={Flame} />
        <Card
          label="Mean Health"
          value={`${((stats.data?.mean_health_score || 0) * 100).toFixed(1)}%`}
          icon={HeartPulse}
        />
        <Card
          label="SLA"
          value={benchmarks.api_sla_met === false ? "Missed" : "Met"}
          icon={ShieldCheck}
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.2fr_.8fr]">
        <Panel title="Wafer Map · Die Heatmap · Cluster Overlay">
          <div className="mb-3 flex flex-wrap gap-2">
            {(
              [
                ["wafer", "Wafer Map"],
                ["heatmap", "Die Heatmap"],
                ["clusters", "Cluster Overlay"],
              ] as const
            ).map(([value, label]) => (
              <button
                key={value}
                onClick={() => setMapMode(value)}
                className={cn(
                  "rounded-lg border px-3 py-1.5 text-xs uppercase tracking-wide",
                  mapMode === value
                    ? "border-[var(--accent)] bg-[var(--accent-soft)] text-white"
                    : "border-white/10 text-[var(--muted)]",
                )}
              >
                {label}
              </button>
            ))}
          </div>
          <DieMapCanvas
            dies={rows}
            hotspots={hotspots.data?.hotspots || []}
            clusters={clusters.data?.clusters || []}
            selected={selected}
            mode={mapMode}
          />
        </Panel>
        <Panel title="Evaluation Benchmark Metrics">
          <div className="grid gap-3 sm:grid-cols-2">
            <Metric
              label="Latency"
              value={`${Number(benchmarks.detection_latency_ms || 0).toFixed(1)} ms`}
            />
            <Metric
              label="Throughput"
              value={`${Number(benchmarks.throughput_records_per_second || 0).toFixed(1)} r/s`}
            />
            <Metric
              label="Precision"
              value={
                benchmarks.precision == null
                  ? "n/a"
                  : `${(Number(benchmarks.precision) * 100).toFixed(1)}%`
              }
            />
            <Metric
              label="Recall"
              value={
                benchmarks.recall == null
                  ? "n/a"
                  : `${(Number(benchmarks.recall) * 100).toFixed(1)}%`
              }
            />
            <Metric
              label="F1"
              value={
                benchmarks.f1_score == null
                  ? "n/a"
                  : Number(benchmarks.f1_score).toFixed(3)
              }
            />
            <Metric
              label="Memory"
              value={`${Number(benchmarks.process_memory_mb || 0).toFixed(1)} MB`}
            />
          </div>
          <div className="mt-4 flex items-center gap-2 text-xs text-[var(--muted)]">
            <Cpu size={14} />
            Hotspots {stats.data?.hotspot_count ?? 0} · Clusters{" "}
            {stats.data?.cluster_count ?? 0} · Isolated{" "}
            {stats.data?.isolated_failures ?? 0}
          </div>
        </Panel>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Panel title="Failure Density">
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={densityData}>
              <CartesianGrid stroke="rgba(255,255,255,.05)" />
              <XAxis dataKey="die" hide />
              <YAxis />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="density" fill="#a78bfa" radius={4} />
            </BarChart>
          </ResponsiveContainer>
        </Panel>
        <Panel title="Die Health Scores">
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={healthData}>
              <CartesianGrid stroke="rgba(255,255,255,.05)" />
              <XAxis dataKey="die" hide />
              <YAxis domain={[0, 100]} />
              <Tooltip contentStyle={tooltipStyle} />
              <Area
                dataKey="health"
                stroke="#34d399"
                fill="rgba(52,211,153,.18)"
              />
              <Area
                dataKey="confidence"
                stroke="#38bdf8"
                fill="rgba(56,189,248,.08)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </Panel>
        <Panel title="Density Trends">
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={trendBuckets}>
              <CartesianGrid stroke="rgba(255,255,255,.05)" />
              <XAxis dataKey="trend" />
              <YAxis allowDecimals={false} />
              <Tooltip contentStyle={tooltipStyle} />
              <Line dataKey="count" stroke="#fb923c" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </Panel>
      </div>

      <section className="glass-panel overflow-hidden rounded-2xl">
        <div className="flex flex-wrap gap-2 border-b border-white/5 p-3">
          <div className="relative min-w-60 flex-1">
            <Search
              size={14}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)]"
            />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search lot, wafer, die, pattern, fault, recommendation"
              className="w-full rounded-lg border border-white/10 bg-black/25 py-2 pl-9 pr-3 text-sm"
            />
          </div>
          <select
            value={severity}
            onChange={(e) => setSeverity(e.target.value)}
            className="input w-36"
          >
            <option value="">All severity</option>
            {["critical", "high", "medium", "low"].map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
          <label className="flex items-center gap-2 rounded-lg border border-white/10 px-3 text-xs text-[var(--muted)]">
            <input
              type="checkbox"
              checked={failingOnly}
              onChange={(e) => setFailingOnly(e.target.checked)}
            />
            Failing only
          </label>
        </div>
        <div className="max-h-[520px] overflow-auto">
          <table className="w-full text-left text-sm">
            <thead className="sticky top-0 bg-[#111827] text-[10px] uppercase text-[var(--muted)]">
              <tr>
                {[
                  "Lot / Wafer / Die",
                  "Density",
                  "Health",
                  "Neighbors",
                  "Trend",
                  "Severity",
                  "Hotspot",
                  "Cluster",
                ].map((label) => (
                  <th key={label} className="px-3 py-2">
                    {label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr
                  key={row.die_result_id}
                  onClick={() => setSelected(row)}
                  className={cn(
                    "cursor-pointer border-t border-white/5 hover:bg-white/5",
                    selected?.die_result_id === row.die_result_id &&
                      "bg-[var(--accent-soft)]",
                  )}
                >
                  <td className="px-3 py-3">
                    <div className="font-medium">{row.die_id}</div>
                    <div className="text-[10px] text-[var(--muted)]">
                      {row.lot_id} · {row.wafer_id}
                    </div>
                  </td>
                  <td className="px-3 py-3 font-mono">
                    {(row.failure_density * 100).toFixed(2)}%
                  </td>
                  <td className="px-3 py-3">
                    {(row.health_score * 100).toFixed(1)}%
                  </td>
                  <td className="px-3 py-3">
                    {row.neighbor_failure_count}
                    {row.is_isolated ? " · iso" : ""}
                  </td>
                  <td className="px-3 py-3">
                    <Badge value={row.trend_status} />
                  </td>
                  <td className="px-3 py-3">
                    <Badge value={row.severity} />
                  </td>
                  <td className="px-3 py-3 font-mono text-[10px]">
                    {row.hotspot_id?.slice(0, 8) || "—"}
                  </td>
                  <td className="px-3 py-3 font-mono text-[10px]">
                    {row.cluster_id?.slice(0, 8) || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="glass-panel rounded-2xl p-5">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
          Engineering Recommendation & Drill-Down
        </h3>
        {selected ? (
          <div className="mt-3 grid gap-4 lg:grid-cols-[1.2fr_.8fr]">
            <div>
              <p className="text-sm leading-6">{selected.engineering_recommendation}</p>
              <p className="mt-2 text-xs text-[var(--muted)]">
                Density {(selected.failure_density * 100).toFixed(2)}% · health{" "}
                {(selected.health_score * 100).toFixed(1)}% · confidence{" "}
                {(selected.confidence_score * 100).toFixed(1)}% · neighbors{" "}
                {selected.neighbor_failure_count} · trend {selected.trend_status}
              </p>
              {(detail.data?.engineering_recommendations || []).length > 0 && (
                <ul className="mt-3 space-y-2">
                  {detail.data?.engineering_recommendations?.map((item) => (
                    <li
                      key={item.recommendation_id}
                      className="rounded-xl border border-white/10 bg-black/20 p-3 text-sm"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-medium">{item.recommendation_code}</span>
                        <Badge value={item.priority} />
                      </div>
                      <p className="mt-1 text-[var(--muted)]">{item.action}</p>
                      <p className="mt-1 text-xs text-[var(--muted)]">{item.rationale}</p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className="rounded-xl border border-white/10 bg-black/20 p-3 text-xs text-[var(--muted)]">
              <div className="mb-2 flex items-center gap-2 text-white">
                <Target size={14} /> Traceability
              </div>
              <pre className="max-h-56 overflow-auto whitespace-pre-wrap font-mono leading-5">
                {JSON.stringify(detail.data?.traceability || selected, null, 2)}
              </pre>
            </div>
          </div>
        ) : (
          <p className="mt-3 text-sm text-[var(--muted)]">
            Select a die for drill-down evidence and engineering recommendations.
          </p>
        )}
      </section>

      <div className="grid gap-3 sm:grid-cols-3">
        <Card
          label="Mean Density"
          value={`${((stats.data?.mean_failure_density || 0) * 100).toFixed(2)}%`}
          icon={Activity}
        />
        <Card
          label="Mean Confidence"
          value={`${((stats.data?.mean_confidence || 0) * 100).toFixed(1)}%`}
          icon={ShieldCheck}
        />
        <Card
          label="Spatial Objects"
          value={`${stats.data?.hotspot_count ?? 0} / ${stats.data?.cluster_count ?? 0}`}
          icon={Flame}
        />
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="text-xs uppercase tracking-wide text-[var(--muted)]">
      {label}
      {children}
    </label>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="glass-panel rounded-2xl p-4">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
        {title}
      </h3>
      {children}
    </section>
  );
}

function Card({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string | number;
  icon: React.ComponentType<{ size?: number }>;
}) {
  return (
    <div className="glass-panel rounded-2xl p-4">
      <div className="flex items-center justify-between text-[var(--muted)]">
        <span className="text-xs uppercase">{label}</span>
        <Icon size={16} />
      </div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-black/20 p-3">
      <div className="text-[10px] uppercase tracking-wide text-[var(--muted)]">{label}</div>
      <div className="mt-1 text-lg font-semibold text-white">{value}</div>
    </div>
  );
}

function Badge({ value }: { value: string }) {
  return (
    <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[10px] uppercase tracking-wide">
      {value.replaceAll("_", " ")}
    </span>
  );
}
