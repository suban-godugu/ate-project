"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Area, AreaChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Braces, Download, GitFork, Play, Search, ShieldCheck, Target, TrendingUp } from "lucide-react";
import {
  analyzeCorrelation,
  getCorrelationHistory,
  getCorrelationStatistics,
  getCorrelationTrends,
  listCorrelations,
  listUploads,
  type CorrelationMetric,
} from "@/lib/api";
import { CorrelationCanvas } from "@/components/CorrelationCanvas";
import { cn } from "@/lib/utils";
import { useAutoSelectFirstId } from "@/hooks/useAutoSelectFirstId";
import { useAutoSelectFirstRow } from "@/hooks/useAutoSelectFirstRow";

const tooltipStyle = { background: "#111827", border: "1px solid rgba(255,255,255,.1)", borderRadius: 10 };

export function CorrelationDashboard() {
  const qc = useQueryClient();
  const [uploadId, setUploadId] = useState("");
  const [search, setSearch] = useState("");
  const [strength, setStrength] = useState("");
  const [severity, setSeverity] = useState("");
  const [threshold, setThreshold] = useState(0.15);
  const [confidence, setConfidence] = useState(0.6);
  const [windowSize, setWindowSize] = useState(50);
  const [selected, setSelected] = useState<CorrelationMetric | null>(null);

  const uploads = useQuery({ queryKey: ["uploads"], queryFn: listUploads });
  useAutoSelectFirstId(
    uploadId,
    setUploadId,
    (uploads.data?.uploads || []).map((u) => u.id),
  );
  const correlations = useQuery({
    queryKey: ["correlations", strength, severity],
    queryFn: () => listCorrelations({ strength: strength || undefined, severity: severity || undefined }),
    refetchInterval: 5000,
  });
  const trends = useQuery({ queryKey: ["correlation-trends"], queryFn: getCorrelationTrends, refetchInterval: 5000 });
  const stats = useQuery({ queryKey: ["correlation-statistics"], queryFn: getCorrelationStatistics, refetchInterval: 5000 });
  const history = useQuery({ queryKey: ["correlation-history"], queryFn: getCorrelationHistory, refetchInterval: 5000 });
  const analyze = useMutation({
    mutationFn: () => analyzeCorrelation({
      upload_id: uploadId,
      coefficient_threshold: threshold,
      confidence_threshold: confidence,
      historical_window: windowSize,
      incremental: true,
    }),
    onSuccess: async () => Promise.all([
      qc.invalidateQueries({ queryKey: ["correlations"] }),
      qc.invalidateQueries({ queryKey: ["correlation-trends"] }),
      qc.invalidateQueries({ queryKey: ["correlation-statistics"] }),
      qc.invalidateQueries({ queryKey: ["correlation-history"] }),
    ]),
  });

  const rows = useMemo(() => {
    const values = correlations.data?.correlations || [];
    const query = search.toLowerCase();
    return query
      ? values.filter((row) => `${row.pattern_id} ${row.fault_type} ${row.engineering_recommendation}`.toLowerCase().includes(query))
      : values;
  }, [correlations.data, search]);
  useAutoSelectFirstRow(selected, setSelected, rows);
  const selectedTrend = (trends.data?.trends || []).find((row) => row.correlation_id === selected?.correlation_id);
  const trendData = (selectedTrend?.time_series || []).map((row, index) => ({ execution: index + 1, coefficient: row.coefficient, confidence: selected?.confidence_score || 0 }));
  const confidenceData = rows.slice(0, 18).map((row) => ({ pattern: row.pattern_id.slice(0, 12), confidence: row.confidence_score * 100, coefficient: Math.abs(row.correlation_coefficient) * 100 }));
  const matrix = stats.data?.matrix || { patterns: [], fault_types: [], values: [] };
  const matrixPatterns = Array.isArray(matrix.patterns) ? matrix.patterns : [];
  const matrixFaults = Array.isArray(matrix.fault_types) ? matrix.fault_types : [];
  const matrixValues = Array.isArray(matrix.values) ? matrix.values : [];

  function exportData(format: "json" | "csv") {
    const content = format === "json"
      ? JSON.stringify({ correlations: rows, trends: trends.data?.trends || [], history: history.data?.history || [] }, null, 2)
      : [
          "correlation_id,pattern_id,fault_type,coefficient,strength,confidence,p_value,severity,trend,recommendation",
          ...rows.map((row) => [row.correlation_id, row.pattern_id, JSON.stringify(row.fault_type), row.correlation_coefficient, row.correlation_strength, row.confidence_score, row.p_value, row.severity, row.trend_status, JSON.stringify(row.engineering_recommendation)].join(",")),
        ].join("\n");
    const link = document.createElement("a");
    link.href = URL.createObjectURL(new Blob([content], { type: format === "json" ? "application/json" : "text/csv" }));
    link.download = `fa-fr-006-correlation-${new Date().toISOString()}.${format}`;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  return (
    <div className="space-y-5">
      <header className="glass-panel rounded-2xl p-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-xs font-semibold tracking-[.2em] text-[var(--accent)]">FA-FR-006</p>
            <h1 className="mt-1 text-2xl font-semibold">Failure-to-Pattern Correlation</h1>
            <p className="mt-2 max-w-3xl text-sm text-[var(--muted)]">Statistically significant pattern/fault relationships with lineage, confidence, trend, spatial evidence, and engineering actions.</p>
          </div>
          <div className="flex gap-2">
            <button onClick={() => exportData("json")} className="rounded-xl border border-white/10 px-3 py-2 text-sm"><Braces className="mr-2 inline" size={15} />JSON</button>
            <button onClick={() => exportData("csv")} className="rounded-xl border border-white/10 px-3 py-2 text-sm"><Download className="mr-2 inline" size={15} />CSV</button>
          </div>
        </div>
      </header>

      <section className="glass-panel grid gap-3 rounded-2xl p-4 xl:grid-cols-[1fr_130px_130px_120px_auto]">
        <Field label="Completed FA-FR-001 → 005 upload">
          <select value={uploadId} onChange={(e) => setUploadId(e.target.value)} className="input">
            <option value="">Select upload</option>
            {(uploads.data?.uploads || []).filter((row) => row.status === "completed").map((row) => <option key={row.id} value={row.id}>{row.original_filename}</option>)}
          </select>
        </Field>
        <Field label="Coefficient">
          <input className="input" type="number" min={0} max={1} step={0.01} value={threshold} onChange={(e) => setThreshold(Number(e.target.value))} />
        </Field>
        <Field label="Confidence">
          <input className="input" type="number" min={0} max={1} step={0.01} value={confidence} onChange={(e) => setConfidence(Number(e.target.value))} />
        </Field>
        <Field label="History">
          <input className="input" type="number" min={2} max={500} value={windowSize} onChange={(e) => setWindowSize(Number(e.target.value))} />
        </Field>
        <button disabled={!uploadId || analyze.isPending} onClick={() => analyze.mutate()} className="self-end rounded-xl bg-[var(--accent)] px-4 py-2 text-sm font-medium disabled:opacity-40"><Play className="mr-2 inline" size={15} />{analyze.isPending ? "Analyzing…" : "Run Correlation"}</button>
        {analyze.error && <p className="text-xs text-red-300 xl:col-span-5">{String(analyze.error)}</p>}
      </section>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Card label="Significant Relationships" value={stats.data?.correlation_count ?? 0} icon={GitFork} />
        <Card label="Strong Correlations" value={stats.data?.strong_count ?? 0} icon={Target} />
        <Card label="Mean Confidence" value={`${((stats.data?.mean_confidence || 0) * 100).toFixed(1)}%`} icon={ShieldCheck} />
        <Card label="SLA" value={stats.data?.benchmark_metrics?.api_sla_met === false ? "Missed" : "Met"} icon={TrendingUp} />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Panel title="Failure-to-Pattern Correlation Matrix">
          <div className="h-[300px] overflow-auto">
            <div className="grid gap-1" style={{ gridTemplateColumns: `120px repeat(${Math.max(1, matrixPatterns.length)}, minmax(70px,1fr))` }}>
              <div />
              {matrixPatterns.map((pattern: string) => <div key={pattern} className="truncate p-1 text-center text-[10px] text-[var(--muted)]">{pattern}</div>)}
              {matrixFaults.map((fault: string, row: number) => [
                <div key={`${fault}-label`} className="truncate p-2 text-[10px]">{fault}</div>,
                ...matrixPatterns.map((pattern: string, column: number) => {
                  const value = Number(matrixValues[row]?.[column] || 0);
                  return <div key={`${fault}-${pattern}`} title={`${fault} × ${pattern}: ${value.toFixed(4)}`} className="rounded p-2 text-center text-[10px]" style={{ background: value < 0 ? `rgba(248,113,113,${Math.abs(value)})` : `rgba(56,189,248,${Math.abs(value)})` }}>{value.toFixed(2)}</div>;
                }),
              ])}
            </div>
          </div>
        </Panel>
        <Panel title="Pattern Relationship Graph · Wafer Overlay">
          <CorrelationCanvas rows={rows} selected={selected} />
        </Panel>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Panel title="Confidence Score Dashboard">
          <ResponsiveContainer width="100%" height={270}><AreaChart data={confidenceData}><CartesianGrid stroke="rgba(255,255,255,.05)" /><XAxis dataKey="pattern" hide /><YAxis domain={[0, 100]} /><Tooltip contentStyle={tooltipStyle} /><Area dataKey="confidence" stroke="#34d399" fill="rgba(52,211,153,.15)" /><Area dataKey="coefficient" stroke="#38bdf8" fill="rgba(56,189,248,.08)" /></AreaChart></ResponsiveContainer>
        </Panel>
        <Panel title="Correlation Trend">
          <ResponsiveContainer width="100%" height={270}><LineChart data={trendData}><CartesianGrid stroke="rgba(255,255,255,.05)" /><XAxis dataKey="execution" /><YAxis domain={[-1, 1]} /><Tooltip contentStyle={tooltipStyle} /><Line dataKey="coefficient" stroke="#a78bfa" strokeWidth={3} /></LineChart></ResponsiveContainer>
        </Panel>
      </div>

      <section className="glass-panel overflow-hidden rounded-2xl">
        <div className="flex flex-wrap gap-2 border-b border-white/5 p-3">
          <div className="relative min-w-60 flex-1"><Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)]" /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search pattern, fault, recommendation" className="w-full rounded-lg border border-white/10 bg-black/25 py-2 pl-9 pr-3 text-sm" /></div>
          <select value={strength} onChange={(e) => setStrength(e.target.value)} className="input w-40"><option value="">All strengths</option>{["very_strong", "strong", "moderate", "weak"].map((value) => <option key={value}>{value}</option>)}</select>
          <select value={severity} onChange={(e) => setSeverity(e.target.value)} className="input w-36"><option value="">All severity</option>{["critical", "high", "medium", "low"].map((value) => <option key={value}>{value}</option>)}</select>
        </div>
        <div className="max-h-[520px] overflow-auto">
          <table className="w-full text-left text-sm"><thead className="sticky top-0 bg-[#111827] text-[10px] uppercase text-[var(--muted)]"><tr>{["Pattern / Fault", "Coefficient", "Strength", "Confidence", "p-value", "Failures", "Trend", "Severity"].map((label) => <th key={label} className="px-3 py-2">{label}</th>)}</tr></thead>
            <tbody>{rows.map((row) => <tr key={row.correlation_id} onClick={() => setSelected(row)} className={cn("cursor-pointer border-t border-white/5 hover:bg-white/5", selected?.correlation_id === row.correlation_id && "bg-[var(--accent-soft)]")}><td className="px-3 py-3"><div className="font-medium">{row.pattern_id}</div><div className="text-[10px] text-[var(--muted)]">{row.fault_type}</div></td><td className="px-3 py-3 font-mono">{row.correlation_coefficient.toFixed(4)}</td><td className="px-3 py-3"><Badge value={row.correlation_strength} /></td><td className="px-3 py-3">{(row.confidence_score * 100).toFixed(1)}%</td><td className="px-3 py-3">{row.p_value?.toExponential(2)}</td><td className="px-3 py-3">{row.correlated_failures}</td><td className="px-3 py-3"><Badge value={row.trend_status} /></td><td className="px-3 py-3"><Badge value={row.severity} /></td></tr>)}</tbody>
          </table>
        </div>
      </section>

      <section className="glass-panel rounded-2xl p-5">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">Engineering Recommendation & Explainability</h3>
        {selected ? <div className="mt-3 grid gap-4 md:grid-cols-[1fr_auto]"><div><p className="text-sm leading-6">{selected.engineering_recommendation}</p><p className="mt-2 text-xs text-[var(--muted)]">Coefficient {selected.correlation_coefficient.toFixed(4)} · confidence {(selected.confidence_score * 100).toFixed(1)}% · p {selected.p_value?.toExponential(3)} · n={selected.sample_size}</p></div><Badge value={selected.severity} /></div> : <p className="mt-3 text-sm text-[var(--muted)]">Select a relationship for evidence and an actionable recommendation.</p>}
      </section>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) { return <label className="text-xs uppercase tracking-wide text-[var(--muted)]">{label}{children}</label>; }
function Panel({ title, children }: { title: string; children: React.ReactNode }) { return <section className="glass-panel rounded-2xl p-4"><h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">{title}</h3>{children}</section>; }
function Card({ label, value, icon: Icon }: { label: string; value: string | number; icon: React.ComponentType<{ size?: number }> }) { return <div className="glass-panel rounded-2xl p-4"><div className="flex items-center justify-between text-[var(--muted)]"><span className="text-xs uppercase">{label}</span><Icon size={16} /></div><div className="mt-2 text-2xl font-semibold">{value}</div></div>; }
function Badge({ value }: { value: string }) { return <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[10px] uppercase tracking-wide">{value.replaceAll("_", " ")}</span>; }
