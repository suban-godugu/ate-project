"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  Activity,
  BrainCircuit,
  Braces,
  Download,
  MessageSquarePlus,
  Play,
  Search,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
} from "lucide-react";
import {
  getFaultPrediction,
  getFaultPredictionHistory,
  getFaultPredictionStatistics,
  listFaultPredictions,
  listUploads,
  predictFaultTypes,
  submitFaultPredictionFeedback,
  type FaultPredictionSummary,
} from "@/lib/api";
import {
  FaultPredictionEvidenceCanvas,
  normalizeSupportingEvidence,
} from "@/components/FaultPredictionEvidenceCanvas";
import { cn } from "@/lib/utils";
import { useAutoSelectFirstId } from "@/hooks/useAutoSelectFirstId";
import { useAutoSelectFirstRow } from "@/hooks/useAutoSelectFirstRow";

const tooltipStyle = {
  background: "#111827",
  border: "1px solid rgba(255,255,255,.1)",
  borderRadius: 10,
};

const FAULT_COLORS = ["#a78bfa", "#38bdf8", "#34d399", "#fb923c", "#f472b6", "#facc15"];

export function FaultPredictionDashboard() {
  const qc = useQueryClient();
  const [uploadId, setUploadId] = useState("");
  const [search, setSearch] = useState("");
  const [faultFilter, setFaultFilter] = useState("");
  const [modelVersion, setModelVersion] = useState("");
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.55);
  const [selected, setSelected] = useState<FaultPredictionSummary | null>(null);
  const [feedbackFaultType, setFeedbackFaultType] = useState("");
  const [feedbackCorrect, setFeedbackCorrect] = useState<"yes" | "no" | "">("");
  const [feedbackNotes, setFeedbackNotes] = useState("");

  const uploads = useQuery({ queryKey: ["uploads"], queryFn: listUploads });
  useAutoSelectFirstId(
    uploadId,
    setUploadId,
    (uploads.data?.uploads || []).map((u) => u.id),
  );
  const predictions = useQuery({
    queryKey: ["fault-predictions", faultFilter, modelVersion],
    queryFn: () =>
      listFaultPredictions({
        predicted_fault_type: faultFilter || undefined,
        model_version: modelVersion || undefined,
      }),
    refetchInterval: 5000,
  });
  const stats = useQuery({
    queryKey: ["fault-prediction-statistics"],
    queryFn: getFaultPredictionStatistics,
    refetchInterval: 5000,
  });
  const history = useQuery({
    queryKey: ["fault-prediction-history"],
    queryFn: getFaultPredictionHistory,
    refetchInterval: 5000,
  });
  const detail = useQuery({
    queryKey: ["fault-prediction-detail", selected?.prediction_id],
    queryFn: () => getFaultPrediction(selected!.prediction_id),
    enabled: Boolean(selected?.prediction_id),
  });

  const predict = useMutation({
    mutationFn: () =>
      predictFaultTypes({
        upload_id: uploadId,
        confidence_threshold: confidenceThreshold,
        model_version: modelVersion || undefined,
        incremental: true,
        async_execution: false,
      }),
    onSuccess: async () => {
      await Promise.all([
        qc.invalidateQueries({ queryKey: ["fault-predictions"] }),
        qc.invalidateQueries({ queryKey: ["fault-prediction-statistics"] }),
        qc.invalidateQueries({ queryKey: ["fault-prediction-history"] }),
        qc.invalidateQueries({ queryKey: ["fault-prediction-detail"] }),
      ]);
    },
  });

  const feedback = useMutation({
    mutationFn: () =>
      submitFaultPredictionFeedback({
        prediction_id: selected!.prediction_id,
        actual_fault_type: feedbackFaultType || undefined,
        is_correct: feedbackCorrect === "yes" ? true : feedbackCorrect === "no" ? false : undefined,
        feedback_notes: feedbackNotes || undefined,
      }),
    onSuccess: () => {
      setFeedbackNotes("");
      setFeedbackFaultType("");
      setFeedbackCorrect("");
    },
  });

  const rows = useMemo(() => {
    const items = predictions.data?.predictions || [];
    if (!search) return items;
    const query = search.toLowerCase();
    return items.filter(
      (item) =>
        item.prediction_id.toLowerCase().includes(query) ||
        item.pattern_id.toLowerCase().includes(query) ||
        item.predicted_fault_type.toLowerCase().includes(query) ||
        (item.engineering_explanation || "").toLowerCase().includes(query) ||
        (item.alternative_fault_types || []).some((alt) =>
          (alt.fault_type || "").toLowerCase().includes(query),
        ),
    );
  }, [predictions.data, search]);

  useAutoSelectFirstRow(selected, setSelected, rows);

  const faultTypes = useMemo(() => {
    const set = new Set(rows.map((row) => row.predicted_fault_type));
    return Array.from(set).sort();
  }, [rows]);

  const confidenceChartData = rows.slice(0, 16).map((row) => ({
    pattern: row.pattern_id.slice(0, 12),
    confidence: Number((row.confidence_score * 100).toFixed(1)),
    probability: Number((row.prediction_probability * 100).toFixed(1)),
  }));

  const rankedAlternatives = useMemo(() => {
    if (!selected) return [];
    return [
      {
        rank: 1,
        fault_type: selected.predicted_fault_type,
        probability: selected.prediction_probability,
        primary: true,
      },
      ...(selected.alternative_fault_types || []).map((alt) => ({
        rank: alt.rank,
        fault_type: alt.fault_type,
        probability: alt.probability,
        primary: false,
      })),
    ].sort((a, b) => a.rank - b.rank);
  }, [selected]);

  const pieData = rankedAlternatives.map((row, index) => ({
    name: row.fault_type,
    value: Number((row.probability * 100).toFixed(2)),
    fill: FAULT_COLORS[index % FAULT_COLORS.length],
  }));

  // Prediction runs carry the per-execution counts/latency; /history only carries
  // per-prediction snapshots, so prefer runs and fall back to history entries.
  const historyTrend = useMemo(() => {
    const runs = predictions.data?.runs || [];
    if (runs.length) {
      return runs
        .slice(0, 12)
        .reverse()
        .map((run, index) => ({
          run: `R${index + 1}`,
          predictions: Number(run.total_predictions ?? 0),
          latency: Number(run.processing_ms ?? 0),
          confidence:
            run.average_confidence == null
              ? null
              : Number((run.average_confidence * 100).toFixed(1)),
        }));
    }
    return (history.data?.history || [])
      .slice(0, 12)
      .reverse()
      .map((entry, index) => ({
        run: `R${index + 1}`,
        predictions: Number(entry.prediction_count ?? 1),
        latency: Number(entry.processing_ms ?? 0),
        confidence: entry.benchmark_metrics?.mean_confidence
          ? Number((entry.benchmark_metrics.mean_confidence * 100).toFixed(1))
          : null,
      }));
  }, [predictions.data, history.data]);

  const benchmarks = stats.data?.benchmark_metrics || {};

  const topCards = rows.slice(0, 4);

  function exportData(format: "json" | "csv") {
    const payload = {
      predictions: rows,
      statistics: stats.data || {},
      history: history.data?.history || [],
      selected_detail: detail.data || null,
    };
    const content =
      format === "json"
        ? JSON.stringify(payload, null, 2)
        : [
            "prediction_id,pattern_id,predicted_fault_type,confidence_score,prediction_probability,model_version,prediction_timestamp",
            ...rows.map((row) =>
              [
                row.prediction_id,
                row.pattern_id,
                row.predicted_fault_type,
                row.confidence_score,
                row.prediction_probability,
                row.model_version,
                row.prediction_timestamp || "",
              ].join(","),
            ),
          ].join("\n");
    const link = document.createElement("a");
    link.href = URL.createObjectURL(
      new Blob([content], { type: format === "json" ? "application/json" : "text/csv" }),
    );
    link.download = `fa-fr-009-fault-prediction-${new Date().toISOString()}.${format}`;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  return (
    <div className="space-y-5">
      <header className="glass-panel rounded-2xl p-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-xs font-semibold tracking-[.2em] text-[var(--accent)]">
              FA-FR-009
            </p>
            <h1 className="mt-1 text-2xl font-semibold">AI Fault Type Prediction</h1>
            <p className="mt-2 max-w-3xl text-sm text-[var(--muted)]">
              Ranked fault-type predictions with confidence scoring, explainable
              engineering evidence, investigation steps, historical comparison, and
              feedback capture across the FA-FR-001 → 008 analytics pipeline.
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

      <section className="glass-panel grid gap-3 rounded-2xl p-4 xl:grid-cols-[1fr_120px_120px_110px_auto]">
        <Field label="Completed FA-FR-001 → 008 upload">
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
        <Field label="Confidence">
          <input
            className="input"
            type="number"
            min={0}
            max={1}
            step={0.01}
            value={confidenceThreshold}
            onChange={(e) => setConfidenceThreshold(Number(e.target.value))}
          />
        </Field>
        <Field label="Model version">
          <input
            className="input"
            value={modelVersion}
            onChange={(e) => setModelVersion(e.target.value)}
            placeholder="default"
          />
        </Field>
        <Field label="Fault filter">
          <select
            value={faultFilter}
            onChange={(e) => setFaultFilter(e.target.value)}
            className="input"
          >
            <option value="">All types</option>
            {faultTypes.map((fault) => (
              <option key={fault} value={fault}>
                {fault}
              </option>
            ))}
          </select>
        </Field>
        <button
          disabled={!uploadId || predict.isPending}
          onClick={() => predict.mutate()}
          className="self-end rounded-xl bg-[var(--accent)] px-4 py-2 text-sm font-medium disabled:opacity-40"
        >
          <Play className="mr-2 inline" size={15} />
          {predict.isPending ? "Predicting…" : "Run Prediction"}
        </button>
        {predict.error && (
          <p className="text-xs text-red-300 xl:col-span-5">{String(predict.error)}</p>
        )}
      </section>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Card
          label="Total Predictions"
          value={stats.data?.total_predictions ?? 0}
          icon={BrainCircuit}
        />
        <Card
          label="Mean Confidence"
          value={`${((stats.data?.mean_confidence || 0) * 100).toFixed(1)}%`}
          icon={Sparkles}
        />
        <Card
          label="Unique Fault Types"
          value={stats.data?.unique_fault_types ?? 0}
          icon={Activity}
        />
        <Card
          label="SLA"
          value={benchmarks.api_sla_met === false ? "Missed" : "Met"}
          icon={ShieldCheck}
        />
      </div>

      {topCards.length > 0 && (
        <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {topCards.map((row) => (
            <button
              key={row.prediction_id}
              onClick={() => setSelected(row)}
              className={cn(
                "glass-panel rounded-2xl p-4 text-left transition",
                selected?.prediction_id === row.prediction_id
                  ? "accent-ring bg-[var(--accent-soft)]"
                  : "hover:bg-white/5",
              )}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-[10px] uppercase tracking-wide text-[var(--muted)]">
                  {row.pattern_id.slice(0, 18)}
                </span>
                <Badge value={row.model_version} />
              </div>
              <div className="mt-2 text-lg font-semibold">{row.predicted_fault_type}</div>
              <div className="mt-2 flex items-center gap-3 text-xs text-[var(--muted)]">
                <span>Conf {(row.confidence_score * 100).toFixed(1)}%</span>
                <span>Prob {(row.prediction_probability * 100).toFixed(1)}%</span>
              </div>
            </button>
          ))}
        </section>
      )}

      <div className="grid gap-4 xl:grid-cols-[1.2fr_.8fr]">
        <Panel title="Confidence Score Dashboard">
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={confidenceChartData}>
              <CartesianGrid stroke="rgba(255,255,255,.05)" />
              <XAxis dataKey="pattern" hide />
              <YAxis domain={[0, 100]} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="confidence" fill="#a78bfa" radius={4} name="Confidence %" />
              <Bar dataKey="probability" fill="#38bdf8" radius={4} name="Probability %" />
            </BarChart>
          </ResponsiveContainer>
        </Panel>
        <Panel title="Evaluation Benchmark Metrics">
          <div className="grid gap-3 sm:grid-cols-2">
            <Metric
              label="Top-1 Accuracy"
              value={
                benchmarks.top1_accuracy == null
                  ? "n/a"
                  : `${(Number(benchmarks.top1_accuracy) * 100).toFixed(1)}%`
              }
            />
            <Metric
              label="Top-3 Accuracy"
              value={
                benchmarks.top3_accuracy == null
                  ? "n/a"
                  : `${(Number(benchmarks.top3_accuracy) * 100).toFixed(1)}%`
              }
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
                benchmarks.f1_score == null ? "n/a" : Number(benchmarks.f1_score).toFixed(3)
              }
            />
            <Metric
              label="Latency"
              value={`${Number(benchmarks.prediction_latency_ms || 0).toFixed(1)} ms`}
            />
          </div>
          <div className="mt-4 flex items-center gap-2 text-xs text-[var(--muted)]">
            <TrendingUp size={14} />
            Top fault {stats.data?.top_predicted_fault_type || "n/a"} · Mean prob{" "}
            {((stats.data?.mean_probability || 0) * 100).toFixed(1)}%
          </div>
        </Panel>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Panel title="Ranked Fault Distribution">
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={pieData.length ? pieData : [{ name: "n/a", value: 100, fill: "#334155" }]}
                dataKey="value"
                nameKey="name"
                innerRadius={50}
                outerRadius={80}
                paddingAngle={2}
              >
                {(pieData.length ? pieData : [{ name: "n/a", value: 100, fill: "#334155" }]).map(
                  (entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ),
                )}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
        </Panel>
        <Panel title="Prediction Trend · Historical Comparison">
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={historyTrend}>
              <CartesianGrid stroke="rgba(255,255,255,.05)" />
              <XAxis dataKey="run" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip contentStyle={tooltipStyle} />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="predictions"
                stroke="#34d399"
                strokeWidth={2}
                dot={false}
                name="Predictions"
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="latency"
                stroke="#fb923c"
                strokeWidth={2}
                dot={false}
                name="Latency (ms)"
              />
            </LineChart>
          </ResponsiveContainer>
        </Panel>
        <Panel title="Supporting Evidence · Pattern Bars">
          <FaultPredictionEvidenceCanvas
            evidence={normalizeSupportingEvidence(
              selected?.supporting_evidence || rows[0]?.supporting_evidence || [],
            )}
            selectedLabel={selected?.predicted_fault_type}
          />
        </Panel>
      </div>

      <section className="glass-panel rounded-2xl p-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
            Ranked Prediction Table
          </h3>
          <div className="relative">
            <Search
              size={14}
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)]"
            />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search predictions…"
              className="input pl-9"
            />
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase tracking-wide text-[var(--muted)]">
              <tr className="border-b border-white/10">
                <th className="px-3 py-2">Pattern</th>
                <th className="px-3 py-2">Predicted Fault</th>
                <th className="px-3 py-2">Confidence</th>
                <th className="px-3 py-2">Probability</th>
                <th className="px-3 py-2">Alternatives</th>
                <th className="px-3 py-2">Model</th>
                <th className="px-3 py-2">Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr
                  key={row.prediction_id}
                  onClick={() => setSelected(row)}
                  className={cn(
                    "cursor-pointer border-b border-white/5 transition hover:bg-white/5",
                    selected?.prediction_id === row.prediction_id && "bg-[var(--accent-soft)]",
                  )}
                >
                  <td className="px-3 py-3 font-mono text-xs">{row.pattern_id}</td>
                  <td className="px-3 py-3 font-medium">{row.predicted_fault_type}</td>
                  <td className="px-3 py-3">
                    {(row.confidence_score * 100).toFixed(1)}%
                  </td>
                  <td className="px-3 py-3">
                    {(row.prediction_probability * 100).toFixed(1)}%
                  </td>
                  <td className="px-3 py-3 text-xs text-[var(--muted)]">
                    {row.alternative_fault_types
                      ?.slice(0, 3)
                      .map((alt) => alt.fault_type)
                      .join(", ") || "—"}
                  </td>
                  <td className="px-3 py-3">
                    <Badge value={row.model_version} />
                  </td>
                  <td className="px-3 py-3 text-xs text-[var(--muted)]">
                    {row.prediction_timestamp || row.predicted_at
                      ? new Date(
                          String(row.prediction_timestamp || row.predicted_at),
                        ).toLocaleString()
                      : "—"}
                  </td>
                </tr>
              ))}
              {!rows.length && (
                <tr>
                  <td colSpan={7} className="px-3 py-8 text-center text-[var(--muted)]">
                    No predictions yet. Run prediction on a completed upload.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <div className="grid gap-4 xl:grid-cols-[1.2fr_.8fr]">
        <section className="glass-panel rounded-2xl p-5">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
            Engineering Explanation Panel
          </h3>
          {selected ? (
            <div className="mt-3 space-y-4">
              <p className="text-sm leading-6">{selected.engineering_explanation}</p>
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
                  Recommended Investigation Steps
                </h4>
                <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-[var(--muted)]">
                  {(selected.recommended_investigation_steps || []).map((step, index) => (
                    <li key={`${step}-${index}`}>{step}</li>
                  ))}
                  {!selected.recommended_investigation_steps?.length && (
                    <li>No investigation steps returned for this prediction.</li>
                  )}
                </ol>
              </div>
              {rankedAlternatives.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
                    Ranked Alternatives
                  </h4>
                  <ul className="mt-2 space-y-2">
                    {rankedAlternatives.map((alt) => (
                      <li
                        key={`${alt.rank}-${alt.fault_type}`}
                        className="flex items-center justify-between rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm"
                      >
                        <span>
                          #{alt.rank} {alt.fault_type}
                          {alt.primary ? " (primary)" : ""}
                        </span>
                        <span className="font-mono text-xs">
                          {(alt.probability * 100).toFixed(1)}%
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <p className="mt-3 text-sm text-[var(--muted)]">
              Select a prediction row for engineering explanation and drill-down.
            </p>
          )}
        </section>

        <section className="glass-panel rounded-2xl p-5">
          <h3 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
            <MessageSquarePlus size={14} />
            Feedback Submission Panel
          </h3>
          {selected ? (
            <div className="mt-3 space-y-3">
              <Field label="Actual fault type">
                <input
                  className="input"
                  value={feedbackFaultType}
                  onChange={(e) => setFeedbackFaultType(e.target.value)}
                  placeholder={selected.predicted_fault_type}
                />
              </Field>
              <Field label="Prediction correct?">
                <select
                  className="input"
                  value={feedbackCorrect}
                  onChange={(e) => setFeedbackCorrect(e.target.value as "yes" | "no" | "")}
                >
                  <option value="">Select</option>
                  <option value="yes">Yes</option>
                  <option value="no">No</option>
                </select>
              </Field>
              <Field label="Engineering notes">
                <textarea
                  className="input min-h-20"
                  value={feedbackNotes}
                  onChange={(e) => setFeedbackNotes(e.target.value)}
                  placeholder="Validated diagnosis, lab findings, next actions…"
                />
              </Field>
              <button
                disabled={feedback.isPending}
                onClick={() => feedback.mutate()}
                className="w-full rounded-xl bg-[var(--accent)] px-4 py-2 text-sm font-medium disabled:opacity-40"
              >
                {feedback.isPending ? "Submitting…" : "Submit Feedback"}
              </button>
              {feedback.isSuccess && (
                <p className="text-xs text-emerald-300">Feedback recorded for model learning.</p>
              )}
              {feedback.error && (
                <p className="text-xs text-red-300">{String(feedback.error)}</p>
              )}
            </div>
          ) : (
            <p className="mt-3 text-sm text-[var(--muted)]">
              Select a prediction to submit engineering validation feedback.
            </p>
          )}
        </section>
      </div>

      <section className="glass-panel rounded-2xl p-5">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
          Drill-Down · Traceability
        </h3>
        {selected ? (
          <div className="mt-3 grid gap-4 lg:grid-cols-[1.2fr_.8fr]">
            <div className="rounded-xl border border-white/10 bg-black/20 p-3 text-xs text-[var(--muted)]">
              <div className="mb-2 flex items-center gap-2 text-white">
                <Target size={14} /> Supporting Evidence
              </div>
              <pre className="max-h-56 overflow-auto whitespace-pre-wrap font-mono leading-5">
                {JSON.stringify(selected.supporting_evidence, null, 2)}
              </pre>
            </div>
            <div className="rounded-xl border border-white/10 bg-black/20 p-3 text-xs text-[var(--muted)]">
              <div className="mb-2 flex items-center gap-2 text-white">
                <Target size={14} /> Upstream Lineage
              </div>
              <pre className="max-h-56 overflow-auto whitespace-pre-wrap font-mono leading-5">
                {JSON.stringify(
                  detail.data?.traceability ||
                    detail.data?.upstream_execution_ids ||
                    selected,
                  null,
                  2,
                )}
              </pre>
            </div>
          </div>
        ) : (
          <p className="mt-3 text-sm text-[var(--muted)]">
            Select a prediction for evidence and upstream traceability drill-down.
          </p>
        )}
      </section>
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
