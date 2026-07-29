"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Cell,
} from "recharts";
import {
  BarChart3,
  BrainCircuit,
  Braces,
  Download,
  FileSpreadsheet,
  FileText,
  Filter,
  History,
  Play,
  Search,
  Target,
  TrendingUp,
} from "lucide-react";
import {
  exportReport,
  generateReport,
  getReport,
  getReportHistory,
  getReportTemplates,
  listReports,
  listUploads,
  type ReportArtifact,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import { useAutoSelectFirstId } from "@/hooks/useAutoSelectFirstId";

const tooltipStyle = {
  background: "#111827",
  border: "1px solid rgba(255,255,255,.1)",
  borderRadius: 10,
};

const EXPORT_FORMATS: Array<"pdf" | "html" | "csv" | "xlsx" | "json"> = [
  "pdf",
  "html",
  "csv",
  "xlsx",
  "json",
];

const PIE_COLORS = ["#a78bfa", "#38bdf8", "#34d399", "#fb7185", "#f59e0b"];

export function ReportsDashboard() {
  const qc = useQueryClient();
  const [uploadId, setUploadId] = useState("");
  const [templateId, setTemplateId] = useState("");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);
  const [exportFormat, setExportFormat] =
    useState<"pdf" | "html" | "csv" | "xlsx" | "json">("pdf");

  const uploads = useQuery({ queryKey: ["uploads"], queryFn: listUploads });
  useAutoSelectFirstId(
    uploadId,
    setUploadId,
    (uploads.data?.uploads || []).map((u) => u.id),
  );
  const templates = useQuery({
    queryKey: ["report-templates"],
    queryFn: getReportTemplates,
  });
  const reports = useQuery({
    queryKey: ["reports", statusFilter],
    queryFn: () => listReports({ status: statusFilter || undefined }),
    refetchInterval: 5000,
  });
  const reportHistory = useQuery({
    queryKey: ["reports-history"],
    queryFn: () => getReportHistory(),
    refetchInterval: 5000,
  });
  useAutoSelectFirstId(
    selectedReportId || "",
    setSelectedReportId,
    (reports.data?.reports || []).map((r) => r.report_id),
  );
  const selectedReport = useQuery({
    queryKey: ["report-detail", selectedReportId],
    queryFn: () => getReport(selectedReportId!),
    enabled: Boolean(selectedReportId),
  });

  const generate = useMutation({
    mutationFn: () =>
      generateReport({
        upload_id: uploadId || undefined,
        template_id: templateId || undefined,
        title: "FA-FR-010 Executive Decision Report",
        include_sections: [
          "executive_summary",
          "engineering_summary",
          "benchmarks",
          "ai_prediction_summary",
          "recommendations",
        ],
        async_execution: false,
      }),
    onSuccess: async (data) => {
      setSelectedReportId(data.report_id);
      await Promise.all([
        qc.invalidateQueries({ queryKey: ["reports"] }),
        qc.invalidateQueries({ queryKey: ["reports-history"] }),
      ]);
    },
  });

  const exportMutation = useMutation({
    mutationFn: () =>
      exportReport({
        report_id: selected.report_id,
        format: exportFormat,
      }),
  });

  const rows = useMemo(() => {
    const values = reports.data?.reports || [];
    if (!search) return values;
    const q = search.toLowerCase();
    return values.filter((row) =>
      `${row.report_id} ${row.report_name || ""} ${row.template_id || ""} ${row.status || ""}`
        .toLowerCase()
        .includes(q),
    );
  }, [reports.data, search]);

  const selected = selectedReport.data || rows[0];

  const benchmarkRows = useMemo(() => {
    const metrics = selected?.benchmark_metrics || {};
    const labels = [
      "processing_latency_ms",
      "throughput_records_per_minute",
      "confidence_mean",
      "top1_accuracy",
    ];
    return labels.map((key) => ({
      metric: key.replaceAll("_", " "),
      value: Number(metrics[key] || 0),
    }));
  }, [selected]);

  const recommendationRows = (selected?.recommendations || []).slice(0, 8);
  const aiAlternatives = selected?.prediction_summary?.alternatives || [];
  const pieRows = [
    {
      name: selected?.prediction_summary?.top_fault_type || "primary",
      value: Number((selected?.prediction_summary?.probability || 0) * 100),
    },
    ...aiAlternatives.map((item) => ({
      name: item.fault_type,
      value: Number(item.probability * 100),
    })),
  ].filter((item) => item.value > 0);

  const historyRows = (reportHistory.data?.history || [])
    .slice(0, 14)
    .reverse()
    .map((row, idx) => ({
      run: `R${idx + 1}`,
      duration: Number(row.duration_ms || 0),
      status: row.status,
    }));

  // Legacy reports have no run history rows, but they do ship chart payloads,
  // so the panel falls back to the selected report's own series.
  const [chartKey, setChartKey] = useState("");
  const chartSeries = selected?.chart_series || [];
  const activeSeries =
    chartSeries.find((series) => series.key === chartKey) || chartSeries[0] || null;
  const seriesData = (activeSeries?.points || []).map((point) => ({
    label: point.label,
    value: point.value,
  }));

  const engineeringCards = [
    ["Patterns", selected?.engineering_summary?.pattern_count || 0],
    ["Recurrences", selected?.engineering_summary?.recurring_count || 0],
    ["Correlations", selected?.engineering_summary?.strong_correlations || 0],
    ["Failing Wafers", selected?.engineering_summary?.failing_wafer_count || 0],
  ];

  function downloadInline(content: string, filename: string, mime: string) {
    const link = document.createElement("a");
    link.href = URL.createObjectURL(new Blob([content], { type: mime }));
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  return (
    <div className="space-y-5">
      <header className="glass-panel rounded-2xl p-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-xs font-semibold tracking-[.2em] text-[var(--accent)]">
              FA-FR-010
            </p>
            <h1 className="mt-1 text-2xl font-semibold">
              Reporting & Decision Support Dashboard
            </h1>
            <p className="mt-2 max-w-3xl text-sm text-[var(--muted)]">
              Executive and engineering reporting across FA-FR-001 → 009 outputs with
              benchmark visibility, AI prediction summary, recommendation management, and
              enterprise export workflows.
            </p>
          </div>
          <div className="flex gap-2">
            <button
              className="rounded-xl border border-white/10 px-3 py-2 text-sm"
              onClick={() =>
                downloadInline(
                  JSON.stringify({ reports: rows, history: reportHistory.data?.history }, null, 2),
                  `fa-fr-010-reports-${new Date().toISOString()}.json`,
                  "application/json",
                )
              }
            >
              <Braces className="mr-2 inline" size={15} />
              JSON
            </button>
            <button
              className="rounded-xl border border-white/10 px-3 py-2 text-sm"
              onClick={() =>
                downloadInline(
                  [
                    "report_id,report_name,status,template_id,generated_at",
                    ...rows.map((r) =>
                      [
                        r.report_id,
                        JSON.stringify(r.report_name || ""),
                        r.status || "",
                        r.template_id || "",
                        r.generated_at || r.created_at || "",
                      ].join(","),
                    ),
                  ].join("\n"),
                  `fa-fr-010-reports-${new Date().toISOString()}.csv`,
                  "text/csv",
                )
              }
            >
              <Download className="mr-2 inline" size={15} />
              CSV
            </button>
          </div>
        </div>
      </header>

      <section className="glass-panel grid gap-3 rounded-2xl p-4 xl:grid-cols-[1fr_1fr_auto]">
        <label className="text-xs uppercase tracking-wide text-[var(--muted)]">
          Template selector
          <select
            className="input mt-1 w-full"
            value={templateId}
            onChange={(e) => setTemplateId(e.target.value)}
          >
            <option value="">Default template</option>
            {(templates.data?.templates || []).map((template) => (
              <option key={template.template_id} value={template.template_id}>
                {template.name}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs uppercase tracking-wide text-[var(--muted)]">
          Completed upload source
          <select
            className="input mt-1 w-full"
            value={uploadId}
            onChange={(e) => setUploadId(e.target.value)}
          >
            <option value="">Select upload</option>
            {(uploads.data?.uploads || [])
              .filter((item) => item.status === "completed")
              .map((item) => (
                <option key={item.id} value={item.id}>
                  {item.original_filename}
                </option>
              ))}
          </select>
        </label>
        <button
          type="button"
          disabled={!uploadId || generate.isPending}
          onClick={() => generate.mutate()}
          className="self-end rounded-xl bg-[var(--accent)] px-4 py-2 text-sm font-medium disabled:opacity-40"
        >
          <Play className="mr-2 inline" size={15} />
          {generate.isPending ? "Generating…" : "Generate Report"}
        </button>
      </section>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Card
          label="Executive Risk Score"
          value={Number(selected?.executive_summary?.quality_risk_score || 0).toFixed(2)}
          icon={TrendingUp}
        />
        <Card
          label="Total Failures"
          value={selected?.executive_summary?.total_failures || 0}
          icon={Target}
        />
        <Card
          label="Impacted Wafers"
          value={selected?.executive_summary?.impacted_wafers || 0}
          icon={BarChart3}
        />
        <Card
          label="Top Fault Type"
          value={selected?.prediction_summary?.top_fault_type || "n/a"}
          icon={BrainCircuit}
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.2fr_.8fr]">
        <Panel title="Executive Summary Cards">
          <div className="grid gap-3 md:grid-cols-2">
            <Metric
              label="Overview"
              value={selected?.executive_summary?.overview || "Generate or select report"}
            />
            <Metric
              label="Top Fault Type"
              value={selected?.executive_summary?.top_fault_type || "n/a"}
            />
            <Metric
              label="Status"
              value={selected?.status || "n/a"}
            />
            <Metric
              label="Generated"
              value={selected?.generated_at || selected?.created_at || "n/a"}
            />
          </div>
        </Panel>
        <Panel title="AI Prediction Summary">
          <div className="h-[230px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieRows.length ? pieRows : [{ name: "n/a", value: 100 }]}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={45}
                  outerRadius={75}
                  paddingAngle={2}
                >
                  {(pieRows.length ? pieRows : [{ name: "n/a", value: 100 }]).map(
                    (entry, idx) => (
                      <Cell key={`${entry.name}-${idx}`} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                    ),
                  )}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Panel title="Engineering Summary Panels">
          <div className="grid gap-2">
            {engineeringCards.map(([label, value]) => (
              <div
                key={String(label)}
                className="flex justify-between rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-sm"
              >
                <span className="text-[var(--muted)]">{label}</span>
                <span>{value}</span>
              </div>
            ))}
          </div>
        </Panel>
        <Panel title="Benchmark Dashboard">
          <div className="h-[220px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={benchmarkRows}>
                <CartesianGrid stroke="rgba(255,255,255,.05)" />
                <XAxis dataKey="metric" hide />
                <YAxis />
                <Tooltip contentStyle={tooltipStyle} />
                <Bar dataKey="value" fill="#38bdf8" radius={4} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
        <Panel title="Recommendations Panel">
          <div className="space-y-2">
            {recommendationRows.map((item, idx) => (
              <div key={item.id || idx} className="rounded-lg border border-white/10 bg-black/20 p-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs uppercase text-[var(--muted)]">
                    {item.priority || "normal"}
                  </span>
                  {item.area && <Badge value={item.area} />}
                </div>
                <p className="mt-2 text-sm">{item.action}</p>
                {item.rationale && (
                  <p className="mt-1 text-xs text-[var(--muted)]">{item.rationale}</p>
                )}
              </div>
            ))}
            {!recommendationRows.length && (
              <p className="text-sm text-[var(--muted)]">No recommendations available.</p>
            )}
          </div>
        </Panel>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.35fr_.65fr]">
        <section className="glass-panel overflow-hidden rounded-2xl">
          <div className="flex flex-wrap items-center gap-2 border-b border-white/10 p-3">
            <div className="relative min-w-64 flex-1">
              <Search
                size={14}
                className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)]"
              />
              <input
                className="w-full rounded-lg border border-white/10 bg-black/25 py-2 pl-9 pr-3 text-sm"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search report id, name, template, status…"
              />
            </div>
            <select
              className="input w-40"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">All status</option>
              {["completed", "running", "failed", "draft"].map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
            <span className="rounded-lg border border-white/10 bg-black/20 px-3 py-2 text-xs text-[var(--muted)]">
              <Filter className="mr-1 inline" size={12} />
              Search/filter/drill-down
            </span>
          </div>
          <div className="max-h-[520px] overflow-auto">
            <table className="w-full text-left text-sm">
              <thead className="sticky top-0 bg-[#111827] text-[10px] uppercase text-[var(--muted)]">
                <tr>
                  <th className="px-3 py-2">Report</th>
                  <th className="px-3 py-2">Template</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Generated</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr
                    key={row.report_id}
                    onClick={() => setSelectedReportId(row.report_id)}
                    className={cn(
                      "cursor-pointer border-t border-white/5 hover:bg-white/5",
                      selected?.report_id === row.report_id && "bg-[var(--accent-soft)]",
                    )}
                  >
                    <td className="px-3 py-3">
                      <div className="font-medium">{row.report_name || row.report_id}</div>
                      <div className="text-[10px] text-[var(--muted)]">{row.report_id}</div>
                    </td>
                    <td className="px-3 py-3">{row.template_id || "default"}</td>
                    <td className="px-3 py-3">
                      <Badge value={row.status || "unknown"} />
                    </td>
                    <td className="px-3 py-3 text-[var(--muted)]">
                      {row.generated_at || row.created_at || "n/a"}
                    </td>
                  </tr>
                ))}
                {!rows.length && (
                  <tr>
                    <td className="px-3 py-8 text-center text-[var(--muted)]" colSpan={4}>
                      No reports found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <section className="space-y-4">
          <Panel title="Export Panel">
            <label className="text-xs uppercase tracking-wide text-[var(--muted)]">
              Format
              <select
                className="input mt-1 w-full"
                value={exportFormat}
                onChange={(e) =>
                  setExportFormat(e.target.value as "pdf" | "html" | "csv" | "xlsx" | "json")
                }
              >
                {EXPORT_FORMATS.map((format) => (
                  <option key={format} value={format}>
                    {format}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              disabled={!selected?.report_id || exportMutation.isPending}
              onClick={() => exportMutation.mutate()}
              className="mt-3 w-full rounded-xl bg-[var(--accent)] px-4 py-2 text-sm font-medium disabled:opacity-40"
            >
              <Download className="mr-2 inline" size={15} />
              {exportMutation.isPending ? "Exporting…" : "Export report"}
            </button>
            {exportMutation.data?.download_url && (
              <a
                href={exportMutation.data.download_url}
                className="mt-2 block text-xs text-sky-300 underline"
              >
                Download {exportMutation.data.filename || exportMutation.data.format}
              </a>
            )}
            {exportMutation.data?.content && (
              <button
                className="mt-2 w-full rounded-xl border border-white/10 px-3 py-2 text-xs"
                onClick={() =>
                  downloadInline(
                    exportMutation.data!.content!,
                    exportMutation.data!.filename || `report.${exportMutation.data!.format}`,
                    "text/plain",
                  )
                }
              >
                Save inline export file
              </button>
            )}
          </Panel>

          <Panel title="Interactive Charts">
            {historyRows.length ? (
              <div className="h-[180px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={historyRows}>
                    <CartesianGrid stroke="rgba(255,255,255,.05)" />
                    <XAxis dataKey="run" />
                    <YAxis />
                    <Tooltip contentStyle={tooltipStyle} />
                    <Area dataKey="duration" stroke="#a78bfa" fill="rgba(167,139,250,.2)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            ) : seriesData.length ? (
              <div className="space-y-2">
                <div className="flex flex-wrap gap-1.5">
                  {chartSeries.map((series) => (
                    <button
                      key={series.key}
                      type="button"
                      onClick={() => setChartKey(series.key)}
                      className={cn(
                        "rounded-lg border px-2 py-1 text-[10px] uppercase tracking-wide",
                        activeSeries?.key === series.key
                          ? "border-[var(--accent)] bg-[var(--accent-soft)] text-white"
                          : "border-white/10 text-[var(--muted)]",
                      )}
                    >
                      {series.title}
                    </button>
                  ))}
                </div>
                <div className="h-[180px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={seriesData}>
                      <CartesianGrid stroke="rgba(255,255,255,.05)" />
                      <XAxis dataKey="label" tick={{ fontSize: 10 }} />
                      <YAxis />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Bar dataKey="value" fill="#a78bfa" radius={4} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            ) : (
              <p className="py-10 text-center text-sm text-[var(--muted)]">
                Select a report with chart data to explore its series.
              </p>
            )}
          </Panel>
        </section>
      </div>

      <Panel title="Report History Table">
        <div className="max-h-64 overflow-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase tracking-wide text-[var(--muted)]">
              <tr className="border-b border-white/10">
                <th className="px-3 py-2">Report</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Duration</th>
                <th className="px-3 py-2">Created</th>
              </tr>
            </thead>
            <tbody>
              {(reportHistory.data?.history || []).map((item) => (
                <tr key={item.id} className="border-b border-white/5">
                  <td className="px-3 py-2">
                    <div>{item.report_name || item.report_id || item.id}</div>
                    <div className="text-[10px] text-[var(--muted)]">{item.template_id || "default"}</div>
                  </td>
                  <td className="px-3 py-2">
                    <Badge value={item.status} />
                  </td>
                  <td className="px-3 py-2">{item.duration_ms ?? 0} ms</td>
                  <td className="px-3 py-2 text-[var(--muted)]">{item.created_at || "n/a"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-3 flex items-center gap-2 text-xs text-[var(--muted)]">
          <History size={13} />
          Historical runs keep the reporting trail auditable for decision support.
        </div>
      </Panel>
    </div>
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
      <div className="mt-1 text-sm leading-6">{value}</div>
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
