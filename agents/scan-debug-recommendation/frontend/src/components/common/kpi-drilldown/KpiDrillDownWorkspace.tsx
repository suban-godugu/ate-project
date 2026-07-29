"use client";

import dynamic from "next/dynamic";
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { Download, X } from "lucide-react";
import { fetchKpiWorkspace } from "@/lib/kpiDrillDown/api";
import type { ScanDebugKpiId } from "@/types/kpiDrillDown";
import { KpiScanDebugDecisionPanel } from "./KpiScanDebugDecisionPanel";
import { BrokenChainsAnalytics, ConstraintViolationsAnalytics, ConstraintReviewRecsAnalytics, CoverageImpactAnalytics, TimingViolationsAnalytics, TimingDebugRecsAnalytics, WorstSlackAnalytics, PowerViolationsAnalytics, PowerDebugRecsAnalytics, PeakSwitchingAnalytics, DefectSuspectsAnalytics, InvestigationRecsAnalytics, DefectLocalizationAnalytics, ScanChainConfidenceAnalytics, ScanChainRecsAnalytics } from "./DrillDownAnalytics";

const VizBarChart = dynamic(() => import("./VizBarChart").then((m) => m.VizBarChart), {
  ssr: false,
  loading: () => <div className="h-full animate-pulse rounded-xl bg-white/5" />,
});

function VizPanel({
  type,
  series,
}: {
  type: string;
  series: { label: string; value: number }[];
}) {
  if (type === "wafer") {
    return (
      <div className="grid h-full place-items-center">
        <div className="relative h-56 w-56 rounded-full border border-primary/40 bg-gradient-to-br from-primary/20 to-transparent">
          {series.slice(0, 8).map((s, i) => {
            const angle = (i / 8) * Math.PI * 2;
            const x = 50 + Math.cos(angle) * (20 + (s.value % 20));
            const y = 50 + Math.sin(angle) * (20 + (s.value % 20));
            return (
              <div
                key={`${s.label}-${i}`}
                title={`${s.label}: ${s.value}`}
                className="absolute h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full bg-danger"
                style={{ left: `${x}%`, top: `${y}%` }}
              />
            );
          })}
          <div className="absolute inset-0 grid place-items-center text-xs text-muted">
            Wafer XY Map
          </div>
        </div>
      </div>
    );
  }

  if (type === "gauge") {
    const v = series[0]?.value ?? 87;
    return (
      <div className="grid h-full place-items-center">
        <div className="text-center">
          <div className="font-display text-5xl font-semibold text-primary">{v}%</div>
          <div className="text-sm text-muted">Confidence calibration</div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full min-h-[220px]">
      <div className="mb-2 text-xs uppercase tracking-wide text-slate-400">
        {type.replace(/_/g, " ")} visualization
      </div>
      <VizBarChart series={series} />
    </div>
  );
}

function parseBreakRow(row: {
  result: string;
  lotId?: string;
  dieLabel?: string;
  chain?: string;
  chainName?: string;
  candidateBit?: number | null;
  cellLabel?: string;
  scanLength?: number;
  scanIn?: string;
  scanOut?: string;
}) {
  const fromResult =
    row.result.match(
      /^(Chain\s+\d+|channel\d+).*?bit position\s+(\d+).*?\(cell\s+([^)]+)\)/i,
    ) ?? null;
  const chain =
    row.chain ||
    fromResult?.[1] ||
    (row.chainName ? `Chain ${row.chainName.replace(/channel/i, "")}` : "Chain ?");
  const bit =
    row.candidateBit ??
    (fromResult?.[2] != null ? Number(fromResult[2]) : null);
  const cell = row.cellLabel || fromResult?.[3] || "—";
  const scanLength = row.scanLength && row.scanLength > 0 ? row.scanLength : 234;
  return {
    lotId: row.lotId || "—",
    dieLabel: row.dieLabel || "—",
    chain,
    chainName: row.chainName || "",
    bit,
    cell,
    scanLength,
    scanIn: row.scanIn || "—",
    scanOut: row.scanOut || "—",
    result: row.result,
  };
}

function csvEscape(value: string | number | null | undefined) {
  const text = value == null ? "" : String(value);
  if (/[",\n\r]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

function downloadBreakTableCsv(
  rows: ReturnType<typeof parseBreakRow>[],
  filename = "broken_chains_break_isolation.csv",
) {
  const headers = [
    "#",
    "Lot",
    "Die",
    "Chain",
    "Bit Position",
    "Cell",
    "Scan Length",
    "Scan In",
    "Scan Out",
    "Result",
  ];
  const lines = [
    headers.join(","),
    ...rows.map((row, idx) =>
      [
        idx + 1,
        row.lotId,
        row.dieLabel,
        row.chain,
        row.bit ?? "",
        row.cell,
        row.scanLength,
        row.scanIn,
        row.scanOut,
        row.result,
      ]
        .map(csvEscape)
        .join(","),
    ),
  ];
  const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function ChainBreakViz({
  bit,
  scanLength,
}: {
  bit: number | null;
  scanLength: number;
}) {
  const pct =
    bit == null || scanLength <= 1
      ? 0
      : Math.min(100, Math.max(0, (bit / (scanLength - 1)) * 100));
  return (
    <div className="relative mt-2 h-2 w-full overflow-hidden rounded-full bg-white/10">
      <div
        className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-slate-600/40 to-slate-500/20"
        style={{ width: "100%" }}
      />
      {bit != null ? (
        <div
          className="absolute top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-[#0B1020] bg-danger shadow-[0_0_10px_rgba(239,68,68,0.55)]"
          style={{ left: `${pct}%` }}
          title={`bit ${bit} / ${scanLength}`}
        />
      ) : null}
    </div>
  );
}

function BrokenChainsCleanLayout({
  diagnosisResults,
}: {
  diagnosisResults: {
    result: string;
    lotId?: string;
    dieLabel?: string;
    chain?: string;
    chainName?: string;
    candidateBit?: number | null;
    cellLabel?: string;
    scanLength?: number;
    scanIn?: string;
    scanOut?: string;
  }[];
}) {
  const rows = useMemo(() => diagnosisResults.map(parseBreakRow), [diagnosisResults]);

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-2 sm:p-4">
      <BrokenChainsAnalytics rows={rows} />

      <section>
        <div className="mb-3 flex items-end justify-between gap-3">
          <div>
            <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Break Isolation</div>
            <p className="mt-1 text-sm text-slate-400">
              Localized break position on each scan chain
            </p>
          </div>
          <div className="rounded-xl border border-danger/30 bg-danger/10 px-3 py-1.5 text-center">
            <div className="text-[10px] uppercase tracking-wide text-danger/80">Breaks</div>
            <div className="font-display text-lg font-semibold text-white">{rows.length}</div>
          </div>
        </div>

        <div className="max-h-[42vh] space-y-2.5 overflow-y-auto pr-1">
          {rows.map((row, idx) => (
            <motion.div
              key={`${row.result}-${idx}`}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(idx * 0.015, 0.35) }}
              className="rounded-2xl border border-border/50 bg-[#0E1528]/90 p-4"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-lg bg-primary/20 px-2.5 py-1 font-mono text-xs font-semibold text-primary">
                      {row.chain}
                    </span>
                    <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                      bit {row.bit ?? "—"}
                    </span>
                    <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                      {row.cell}
                    </span>
                  </div>
                  <p className="mt-2 font-mono text-[12px] leading-relaxed text-slate-300 sm:text-[13px]">
                    {row.result}
                  </p>
                </div>
                <div className="w-full max-w-[220px] sm:w-48">
                  <div className="flex justify-between text-[10px] uppercase tracking-wide text-slate-500">
                    <span>SI</span>
                    <span>break</span>
                    <span>SO</span>
                  </div>
                  <ChainBreakViz bit={row.bit} scanLength={row.scanLength} />
                  <div className="mt-1 flex justify-between font-mono text-[10px] text-slate-500">
                    <span>0</span>
                    <span>{row.bit ?? "—"}</span>
                    <span>{row.scanLength - 1}</span>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
          {rows.length === 0 ? (
            <div className="rounded-2xl border border-border/40 py-10 text-center text-sm text-slate-500">
              No breaks localized.
            </div>
          ) : null}
        </div>
      </section>

      <section className="rounded-2xl border border-border/60 bg-[#0E1528]/70 p-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Results Table</div>
            <p className="mt-1 text-sm text-slate-400">
              Downloadable break isolation summary
            </p>
          </div>
          <button
            type="button"
            onClick={() => downloadBreakTableCsv(rows)}
            disabled={rows.length === 0}
            className="inline-flex items-center gap-2 rounded-xl border border-primary/40 bg-primary/15 px-3 py-2 text-sm text-white hover:bg-primary/25 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Download size={16} />
            Download CSV
          </button>
        </div>

        <div className="max-h-[36vh] overflow-auto rounded-xl border border-border/50">
          <table className="min-w-full text-left text-xs sm:text-sm">
            <thead className="sticky top-0 bg-[#121a2e] text-[10px] uppercase tracking-wide text-slate-400">
              <tr>
                <th className="px-3 py-2.5 font-medium">#</th>
                <th className="px-3 py-2.5 font-medium">Lot</th>
                <th className="px-3 py-2.5 font-medium">Die</th>
                <th className="px-3 py-2.5 font-medium">Chain</th>
                <th className="px-3 py-2.5 font-medium">Bit</th>
                <th className="px-3 py-2.5 font-medium">Cell</th>
                <th className="px-3 py-2.5 font-medium">Scan Len</th>
                <th className="px-3 py-2.5 font-medium">Scan In</th>
                <th className="px-3 py-2.5 font-medium">Scan Out</th>
                <th className="px-3 py-2.5 font-medium">Result</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, idx) => (
                <tr key={`table-${row.result}-${idx}`} className="border-t border-border/40 text-slate-300">
                  <td className="px-3 py-2 text-slate-500">{idx + 1}</td>
                  <td className="px-3 py-2 font-mono">{row.lotId}</td>
                  <td className="px-3 py-2 font-mono">{row.dieLabel}</td>
                  <td className="px-3 py-2 font-mono text-primary">{row.chain}</td>
                  <td className="px-3 py-2 font-mono">{row.bit ?? "—"}</td>
                  <td className="px-3 py-2 font-mono">{row.cell}</td>
                  <td className="px-3 py-2 font-mono">{row.scanLength}</td>
                  <td className="px-3 py-2 font-mono text-slate-400">{row.scanIn}</td>
                  <td className="px-3 py-2 font-mono text-slate-400">{row.scanOut}</td>
                  <td className="max-w-[280px] px-3 py-2 font-mono text-[11px] text-slate-400">
                    {row.result}
                  </td>
                </tr>
              ))}
              {rows.length === 0 ? (
                <tr>
                  <td colSpan={10} className="px-3 py-8 text-center text-slate-500">
                    No rows to display.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function downloadScanChainRecsCsv(
  rows: {
    lotId?: string;
    dieLabel?: string;
    chain?: string;
    cellLabel?: string;
    candidateBit?: number | null;
    faultType?: string;
    diagnosisRank?: number;
    historicalMatchCount?: number;
    historicalSimilarity?: number;
    historicalRootCause?: string;
    result: string;
  }[],
  filename = "scan_chain_debug_recommendations.csv",
) {
  const headers = [
    "Rank",
    "Lot",
    "Die",
    "Chain",
    "Cell",
    "Bit",
    "Fault Type",
    "Historical Matches",
    "Similarity",
    "Historical Root Cause",
    "Recommendation",
  ];
  const lines = [
    headers.join(","),
    ...rows.map((row) =>
      [
        row.diagnosisRank ?? "",
        row.lotId ?? "",
        row.dieLabel ?? "",
        row.chain ?? "",
        row.cellLabel ?? "",
        row.candidateBit ?? "",
        row.faultType ?? "",
        row.historicalMatchCount ?? 0,
        row.historicalSimilarity ?? "",
        row.historicalRootCause ?? "",
        row.result,
      ]
        .map(csvEscape)
        .join(","),
    ),
  ];
  const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function ScanChainRecsCleanLayout({
  diagnosisResults,
}: {
  diagnosisResults: {
    result: string;
    lotId?: string;
    dieLabel?: string;
    chain?: string;
    cellLabel?: string;
    candidateBit?: number | null;
    faultType?: string;
    diagnosisRank?: number;
    historicalMatchCount?: number;
    historicalSimilarity?: number;
    historicalRootCause?: string;
    failCount?: number;
  }[];
}) {
  const rows = useMemo(
    () =>
      [...diagnosisResults].sort(
        (a, b) => (a.diagnosisRank ?? 999) - (b.diagnosisRank ?? 999),
      ),
    [diagnosisResults],
  );

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-2 sm:p-4">
      <ScanChainRecsAnalytics rows={rows} />

      <section>
        <div className="mb-3 flex items-end justify-between gap-3">
          <div>
            <div className="text-[10px] uppercase tracking-[0.16em] text-primary">
              Recommendations
            </div>
            <p className="mt-1 text-sm text-slate-400">
              Inspect Scan Chain actions from break isolation + diagnosis + historical signature match
            </p>
          </div>
          <div className="rounded-xl border border-primary/30 bg-primary/10 px-3 py-1.5 text-center">
            <div className="text-[10px] uppercase tracking-wide text-primary/80">Recs</div>
            <div className="font-display text-lg font-semibold text-white">{rows.length}</div>
          </div>
        </div>

        <div className="max-h-[42vh] space-y-2.5 overflow-y-auto pr-1">
          {rows.map((row, idx) => (
            <motion.div
              key={`${row.result}-${idx}`}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(idx * 0.015, 0.35) }}
              className="rounded-2xl border border-border/50 bg-[#0E1528]/90 p-4"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-lg bg-danger/20 px-2.5 py-1 font-mono text-xs font-semibold text-danger">
                  rank {row.diagnosisRank ?? "—"}
                </span>
                <span className="rounded-lg bg-primary/20 px-2.5 py-1 font-mono text-xs font-semibold text-primary">
                  {row.chain ?? "Chain ?"}
                </span>
                <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                  {row.cellLabel ?? "—"}
                </span>
                <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                  {row.faultType ?? "stuck-at-0"}
                </span>
                {(row.historicalMatchCount ?? 0) > 0 ? (
                  <span className="rounded-lg border border-success/40 bg-success/10 px-2.5 py-1 font-mono text-xs text-success">
                    {row.historicalMatchCount} hist · sim{" "}
                    {Math.round((row.historicalSimilarity ?? 0) * 100)}%
                  </span>
                ) : (
                  <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-500">
                    no hist match
                  </span>
                )}
              </div>
              <p className="mt-3 text-[13px] leading-relaxed text-slate-200 sm:text-sm">
                {row.result}
              </p>
              <div className="mt-2 text-[11px] text-slate-500">
                {row.lotId}/{row.dieLabel}
                {row.historicalRootCause ? ` · fix: ${row.historicalRootCause}` : ""}
              </div>
            </motion.div>
          ))}
          {rows.length === 0 ? (
            <div className="rounded-2xl border border-border/40 py-10 text-center text-sm text-slate-500">
              No recommendations.
            </div>
          ) : null}
        </div>
      </section>

      <section className="rounded-2xl border border-border/60 bg-[#0E1528]/70 p-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Results Table</div>
            <p className="mt-1 text-sm text-slate-400">
              Downloadable scan chain debug recommendations
            </p>
          </div>
          <button
            type="button"
            onClick={() => downloadScanChainRecsCsv(rows)}
            disabled={rows.length === 0}
            className="inline-flex items-center gap-2 rounded-xl border border-primary/40 bg-primary/15 px-3 py-2 text-sm text-white hover:bg-primary/25 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Download size={16} />
            Download CSV
          </button>
        </div>

        <div className="max-h-[36vh] overflow-auto rounded-xl border border-border/50">
          <table className="min-w-full text-left text-xs sm:text-sm">
            <thead className="sticky top-0 bg-[#121a2e] text-[10px] uppercase tracking-wide text-slate-400">
              <tr>
                <th className="px-3 py-2.5 font-medium">Rank</th>
                <th className="px-3 py-2.5 font-medium">Lot</th>
                <th className="px-3 py-2.5 font-medium">Die</th>
                <th className="px-3 py-2.5 font-medium">Chain</th>
                <th className="px-3 py-2.5 font-medium">Cell</th>
                <th className="px-3 py-2.5 font-medium">Fault</th>
                <th className="px-3 py-2.5 font-medium">Hist</th>
                <th className="px-3 py-2.5 font-medium">Sim</th>
                <th className="px-3 py-2.5 font-medium">Recommendation</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, idx) => (
                <tr key={`rec-table-${idx}`} className="border-t border-border/40 text-slate-300">
                  <td className="px-3 py-2 font-mono text-danger">{row.diagnosisRank}</td>
                  <td className="px-3 py-2 font-mono">{row.lotId}</td>
                  <td className="px-3 py-2 font-mono">{row.dieLabel}</td>
                  <td className="px-3 py-2 font-mono text-primary">{row.chain}</td>
                  <td className="px-3 py-2 font-mono">{row.cellLabel}</td>
                  <td className="px-3 py-2 font-mono">{row.faultType}</td>
                  <td className="px-3 py-2 font-mono">{row.historicalMatchCount ?? 0}</td>
                  <td className="px-3 py-2 font-mono">
                    {row.historicalSimilarity != null
                      ? `${Math.round(row.historicalSimilarity * 100)}%`
                      : "—"}
                  </td>
                  <td className="max-w-[360px] px-3 py-2 text-[11px] text-slate-400">{row.result}</td>
                </tr>
              ))}
              {rows.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-3 py-8 text-center text-slate-500">
                    No rows to display.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function downloadConfidenceCsv(
  rows: {
    rank?: number;
    lotId?: string;
    dieLabel?: string;
    chain?: string;
    cellLabel?: string;
    candidateBit?: number | null;
    confidencePct?: number;
    patternConsistent?: number;
    patternTotal?: number;
    ambiguityGroup?: number;
    historicalMatchCount?: number;
    historicalSimilarity?: number;
    result: string;
  }[],
  filename = "scan_chain_confidence.csv",
) {
  const headers = [
    "Rank",
    "Lot",
    "Die",
    "Chain",
    "Cell",
    "Bit",
    "Confidence %",
    "Patterns Consistent",
    "Total Shift Patterns",
    "Ambiguity Group",
    "Historical Matches",
    "Historical Similarity",
    "Result",
  ];
  const lines = [
    headers.join(","),
    ...rows.map((row) =>
      [
        row.rank ?? "",
        row.lotId ?? "",
        row.dieLabel ?? "",
        row.chain ?? "",
        row.cellLabel ?? "",
        row.candidateBit ?? "",
        row.confidencePct ?? "",
        row.patternConsistent ?? "",
        row.patternTotal ?? "",
        row.ambiguityGroup ?? "",
        row.historicalMatchCount ?? 0,
        row.historicalSimilarity ?? "",
        row.result,
      ]
        .map(csvEscape)
        .join(","),
    ),
  ];
  const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function ScanChainConfidenceCleanLayout({
  diagnosisResults,
}: {
  diagnosisResults: {
    result: string;
    rank?: number;
    lotId?: string;
    dieLabel?: string;
    chain?: string;
    cellLabel?: string;
    candidateBit?: number | null;
    confidencePct?: number;
    patternConsistent?: number;
    patternTotal?: number;
    ambiguityGroup?: number;
    historicalMatchCount?: number;
    historicalSimilarity?: number;
    historicalBoost?: number;
  }[];
}) {
  const rows = useMemo(
    () => [...diagnosisResults].sort((a, b) => (a.rank ?? 999) - (b.rank ?? 999)),
    [diagnosisResults],
  );

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-2 sm:p-4">
      <div className="rounded-2xl border border-primary/30 bg-primary/5 p-4">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Weighted Score</div>
        <p className="mt-2 text-sm text-slate-300">
          pattern consistency (0–1) × (1 / ambiguity group) × historical similarity boost
        </p>
        <p className="mt-1 text-xs text-slate-500">
          Inputs: consistent failing patterns / total shift patterns · diagnosis ambiguity group size ·
          historical case match strength
        </p>
      </div>

      <ScanChainConfidenceAnalytics rows={rows} />

      <section>
        <div className="mb-3 flex items-end justify-between gap-3">
          <div>
            <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Confidence Scores</div>
            <p className="mt-1 text-sm text-slate-400">
              Per-die weighted confidence with pattern, ambiguity, and historical breakdown
            </p>
          </div>
          <div className="rounded-xl border border-primary/30 bg-primary/10 px-3 py-1.5 text-center">
            <div className="text-[10px] uppercase tracking-wide text-primary/80">Dies</div>
            <div className="font-display text-lg font-semibold text-white">{rows.length}</div>
          </div>
        </div>

        <div className="max-h-[42vh] space-y-2.5 overflow-y-auto pr-1">
          {rows.map((row, idx) => (
            <motion.div
              key={`${row.result}-${idx}`}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(idx * 0.015, 0.35) }}
              className="rounded-2xl border border-border/50 bg-[#0E1528]/90 p-4"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-lg bg-primary/20 px-2.5 py-1 font-mono text-xs font-semibold text-primary">
                  {row.confidencePct ?? "—"}%
                </span>
                <span className="rounded-lg bg-primary/20 px-2.5 py-1 font-mono text-xs font-semibold text-primary">
                  {row.chain ?? "Chain ?"}
                </span>
                <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                  {row.cellLabel ?? "—"}
                </span>
                <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                  {row.patternConsistent}/{row.patternTotal} patterns
                </span>
                <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                  ambiguity={row.ambiguityGroup ?? "—"}
                </span>
                <span className="rounded-lg border border-success/40 bg-success/10 px-2.5 py-1 font-mono text-xs text-success">
                  {row.historicalMatchCount ?? 0} hist match
                  {row.historicalSimilarity != null
                    ? ` · ${Math.round(row.historicalSimilarity * 100)}%`
                    : ""}
                </span>
              </div>
              <p className="mt-3 text-[13px] leading-relaxed text-slate-200 sm:text-sm">{row.result}</p>
              <div className="mt-2 text-[11px] text-slate-500">
                {row.lotId}/{row.dieLabel}
                {row.historicalBoost != null
                  ? ` · hist boost ×${Number(row.historicalBoost).toFixed(2)}`
                  : ""}
              </div>
            </motion.div>
          ))}
          {rows.length === 0 ? (
            <div className="rounded-2xl border border-border/40 py-10 text-center text-sm text-slate-500">
              No confidence scores.
            </div>
          ) : null}
        </div>
      </section>

      <section className="rounded-2xl border border-border/60 bg-[#0E1528]/70 p-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Results Table</div>
            <p className="mt-1 text-sm text-slate-400">Downloadable scan chain confidence summary</p>
          </div>
          <button
            type="button"
            onClick={() => downloadConfidenceCsv(rows)}
            disabled={rows.length === 0}
            className="inline-flex items-center gap-2 rounded-xl border border-primary/40 bg-primary/15 px-3 py-2 text-sm text-white hover:bg-primary/25 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Download size={16} />
            Download CSV
          </button>
        </div>

        <div className="max-h-[36vh] overflow-auto rounded-xl border border-border/50">
          <table className="min-w-full text-left text-xs sm:text-sm">
            <thead className="sticky top-0 bg-[#121a2e] text-[10px] uppercase tracking-wide text-slate-400">
              <tr>
                <th className="px-3 py-2.5 font-medium">Rank</th>
                <th className="px-3 py-2.5 font-medium">Lot</th>
                <th className="px-3 py-2.5 font-medium">Die</th>
                <th className="px-3 py-2.5 font-medium">Chain</th>
                <th className="px-3 py-2.5 font-medium">Conf %</th>
                <th className="px-3 py-2.5 font-medium">Patterns</th>
                <th className="px-3 py-2.5 font-medium">Ambiguity</th>
                <th className="px-3 py-2.5 font-medium">Hist</th>
                <th className="px-3 py-2.5 font-medium">Result</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, idx) => (
                <tr key={`conf-table-${idx}`} className="border-t border-border/40 text-slate-300">
                  <td className="px-3 py-2 font-mono text-primary">{row.rank}</td>
                  <td className="px-3 py-2 font-mono">{row.lotId}</td>
                  <td className="px-3 py-2 font-mono">{row.dieLabel}</td>
                  <td className="px-3 py-2 font-mono text-primary">{row.chain}</td>
                  <td className="px-3 py-2 font-mono text-primary">{row.confidencePct}%</td>
                  <td className="px-3 py-2 font-mono">
                    {row.patternConsistent}/{row.patternTotal}
                  </td>
                  <td className="px-3 py-2 font-mono">{row.ambiguityGroup}</td>
                  <td className="px-3 py-2 font-mono">{row.historicalMatchCount ?? 0}</td>
                  <td className="max-w-[360px] px-3 py-2 text-[11px] text-slate-400">{row.result}</td>
                </tr>
              ))}
              {rows.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-3 py-8 text-center text-slate-500">
                    No rows to display.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function ExpandablePatternIds({ labels }: { labels: string[] }) {
  const [expanded, setExpanded] = useState(false);
  const previewCount = 12;
  const hasMore = labels.length > previewCount;
  const visible = expanded || !hasMore ? labels : labels.slice(0, previewCount);
  const hiddenCount = labels.length - previewCount;

  return (
    <div className="mt-2 text-[11px] text-slate-400">
      <span className="text-slate-500">Pattern IDs: </span>
      <span className="font-mono text-slate-300">{visible.join(", ")}</span>
      {hasMore ? (
        <>
          {!expanded ? <span className="font-mono text-slate-500"> … </span> : null}
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="ml-1 inline rounded border border-primary/40 bg-primary/10 px-1.5 py-0.5 font-mono text-[10px] text-primary hover:bg-primary/20"
          >
            {expanded ? "show less" : `+${hiddenCount} more`}
          </button>
        </>
      ) : null}
    </div>
  );
}

function ConstraintViolationsCleanLayout({
  diagnosisResults,
}: {
  diagnosisResults: {
    result: string;
    rank?: number;
    lotId?: string;
    dieLabel?: string;
    heldPins?: string;
    fanoutSignal?: string;
    failingPatternCount?: number;
    totalFailingPatterns?: number;
    procedure?: string;
    usedLotDifferential?: boolean;
    lotDifferentialPatterns?: number;
    affectedDies?: number;
    constraintCategory?: string;
    constraintCategoryLabel?: string;
    constraintPin?: string;
    patternLabels?: string[];
  }[];
}) {
  const rows = useMemo(
    () => [...diagnosisResults].sort((a, b) => (a.rank ?? 999) - (b.rank ?? 999)),
    [diagnosisResults],
  );

  const byCategory = useMemo(() => {
    const map = new Map<string, number>();
    for (const row of rows) {
      const key = row.constraintCategoryLabel ?? row.constraintCategory ?? "Other";
      map.set(key, (map.get(key) ?? 0) + 1);
    }
    return [...map.entries()];
  }, [rows]);

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-2 sm:p-4">
      <div className="rounded-2xl border border-primary/30 bg-primary/5 p-4">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Constraint Categories</div>
        <p className="mt-2 text-sm text-slate-300">
          Typed ATPG over-constraints from STIL held pins: Reset, Scan Enable, and Clock
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {byCategory.map(([label, n]) => (
            <span
              key={label}
              className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-200"
            >
              {label}: {n}
            </span>
          ))}
        </div>
      </div>

      <ConstraintViolationsAnalytics rows={rows} />

      <section>
        <div className="mb-3 flex items-end justify-between gap-3">
          <div>
            <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Constraint Violations</div>
            <p className="mt-1 text-sm text-slate-400">
              One finding per category × held pin × fan-out cone
            </p>
          </div>
          <div className="rounded-xl border border-primary/30 bg-primary/10 px-3 py-1.5 text-center">
            <div className="text-[10px] uppercase tracking-wide text-primary/80">Violations</div>
            <div className="font-display text-lg font-semibold text-white">{rows.length}</div>
          </div>
        </div>

        <div className="max-h-[42vh] space-y-2.5 overflow-y-auto pr-1">
          {rows.map((row, idx) => (
            <motion.div
              key={`${row.constraintCategory}-${row.heldPins}-${row.fanoutSignal}-${idx}`}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(idx * 0.015, 0.35) }}
              className="rounded-2xl border border-border/50 bg-[#0E1528]/90 p-4"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-lg bg-primary/20 px-2.5 py-1 font-mono text-xs font-semibold text-primary">
                  {row.constraintCategoryLabel ?? row.constraintCategory ?? "Constraint"}
                </span>
                <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                  {row.heldPins ?? "—"}
                </span>
                <span className="rounded-lg bg-warning/20 px-2.5 py-1 font-mono text-xs font-semibold text-warning">
                  {row.fanoutSignal ?? "fan-out ?"}
                </span>
                <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                  {row.failingPatternCount ?? "—"} patterns
                </span>
                <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                  {row.affectedDies ?? 1} dies
                </span>
              </div>
              <p className="mt-3 text-[13px] leading-relaxed text-slate-200 sm:text-sm">{row.result}</p>
              {(row.patternLabels?.length ?? 0) > 0 ? (
                <ExpandablePatternIds labels={row.patternLabels ?? []} />
              ) : null}
              <div className="mt-2 text-[11px] text-slate-500">
                example {row.lotId}/{row.dieLabel}
              </div>
            </motion.div>
          ))}
          {rows.length === 0 ? (
            <div className="rounded-2xl border border-border/50 bg-[#0E1528]/90 p-8 text-center text-slate-500">
              No suspected over-constraint patterns detected.
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}

function ConstraintReviewRecsCleanLayout({
  diagnosisResults,
}: {
  diagnosisResults: {
    result: string;
    rank?: number;
    lotId?: string;
    dieLabel?: string;
    heldPins?: string;
    fanoutSignal?: string;
    failingPatternCount?: number;
    procedure?: string;
    affectedDies?: number;
    constraintCategory?: string;
    constraintCategoryLabel?: string;
    patternLabels?: string[];
    historicalMatchCount?: number;
    historicalResolution?: string;
    recommendedAction?: string;
    chainsAffected?: number;
    totalChains?: number;
  }[];
}) {
  const rows = useMemo(
    () => [...diagnosisResults].sort((a, b) => (a.rank ?? 999) - (b.rank ?? 999)),
    [diagnosisResults],
  );

  const byCategory = useMemo(() => {
    const map = new Map<string, number>();
    for (const row of rows) {
      const key = row.constraintCategoryLabel ?? row.constraintCategory ?? "Other";
      map.set(key, (map.get(key) ?? 0) + 1);
    }
    return [...map.entries()];
  }, [rows]);

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-2 sm:p-4">
      <div className="rounded-2xl border border-primary/30 bg-primary/5 p-4">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Review Recommendations</div>
        <p className="mt-2 text-sm text-slate-300">
          Category-specific ATPG review from STIL held pins × failing fan-out, plus historical resolution cites
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {byCategory.map(([label, n]) => (
            <span
              key={label}
              className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-200"
            >
              {label}: {n}
            </span>
          ))}
        </div>
      </div>

      <ConstraintReviewRecsAnalytics rows={rows} />

      <section>
        <div className="mb-3 flex items-end justify-between gap-3">
          <div>
            <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Recommended Reviews</div>
            <p className="mt-1 text-sm text-slate-400">
              Reset / Scan Enable / Clock narratives with candidate pin and historical outcome
            </p>
          </div>
          <div className="rounded-xl border border-primary/30 bg-primary/10 px-3 py-1.5 text-center">
            <div className="text-[10px] uppercase tracking-wide text-primary/80">Recs</div>
            <div className="font-display text-lg font-semibold text-white">{rows.length}</div>
          </div>
        </div>

        <div className="max-h-[42vh] space-y-2.5 overflow-y-auto pr-1">
          {rows.map((row, idx) => (
            <motion.div
              key={`${row.constraintCategory}-${row.heldPins}-${row.fanoutSignal}-${idx}`}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(idx * 0.015, 0.35) }}
              className="rounded-2xl border border-border/50 bg-[#0E1528]/90 p-4"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-lg bg-primary/20 px-2.5 py-1 font-mono text-xs font-semibold text-primary">
                  {row.constraintCategoryLabel ?? "Constraint"}
                </span>
                <span className="rounded-lg border border-success/40 bg-success/10 px-2.5 py-1 font-mono text-xs text-success">
                  {row.recommendedAction ?? "Review"}
                </span>
                <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                  {row.heldPins ?? "—"}
                </span>
                <span className="rounded-lg bg-warning/20 px-2.5 py-1 font-mono text-xs font-semibold text-warning">
                  {row.fanoutSignal ?? "fan-out ?"}
                </span>
                <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                  {row.historicalMatchCount ?? 0} hist
                </span>
              </div>
              <p className="mt-3 text-[13px] leading-relaxed text-slate-200 sm:text-sm">{row.result}</p>
              {(row.patternLabels?.length ?? 0) > 0 ? (
                <ExpandablePatternIds labels={row.patternLabels ?? []} />
              ) : null}
              <div className="mt-2 text-[11px] text-slate-500">
                example {row.lotId}/{row.dieLabel}
                {row.procedure ? ` · ${row.procedure}` : ""}
                {row.chainsAffected != null && row.totalChains != null
                  ? ` · ${row.chainsAffected}/${row.totalChains} chains`
                  : ""}
              </div>
            </motion.div>
          ))}
          {rows.length === 0 ? (
            <div className="rounded-2xl border border-border/50 bg-[#0E1528]/90 p-8 text-center text-slate-500">
              No review recommendations detected.
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}

function CoverageImpactCleanLayout({
  diagnosisResults,
}: {
  diagnosisResults: {
    result: string;
    rank?: number;
    lotId?: string;
    dieLabel?: string;
    heldPins?: string;
    fanoutSignal?: string;
    signature?: string;
    coverageImpactPct?: number;
    associatedPatterns?: number;
    totalFailingPatterns?: number;
    constraintCategory?: string;
    constraintCategoryLabel?: string;
    patternLabels?: string[];
    affectedDies?: number;
    estimateOnly?: boolean;
    scope?: string;
  }[];
}) {
  const rows = useMemo(
    () => [...diagnosisResults].sort((a, b) => (a.rank ?? 999) - (b.rank ?? 999)),
    [diagnosisResults],
  );

  const byCategory = useMemo(() => {
    const map = new Map<string, number>();
    for (const row of rows) {
      if (row.scope && row.scope !== "signature") continue;
      const key = row.constraintCategoryLabel ?? row.constraintCategory ?? "Other";
      map.set(key, (map.get(key) ?? 0) + 1);
    }
    return [...map.entries()];
  }, [rows]);

  const overall = rows.find((r) => r.scope === "overall");

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-2 sm:p-4">
      <div className="rounded-2xl border border-primary/30 bg-primary/5 p-4">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Coverage Impact</div>
        <p className="mt-2 text-sm text-slate-300">
          Whole-dataset share of failing patterns tied to ATPG constraints (Reset / Scan Enable / Clock)
        </p>
        <p className="mt-1 text-xs text-slate-500">
          Card value = overall impact across all constraints. Rows below also break out each category and
          each signature — estimate only (not ATPG fault coverage).
        </p>
        {overall ? (
          <p className="mt-3 rounded-xl border border-primary/30 bg-primary/10 px-3 py-2 font-mono text-sm text-primary">
            Overall: ~{overall.coverageImpactPct}% ({overall.associatedPatterns}/
            {overall.totalFailingPatterns} failing patterns)
          </p>
        ) : null}
        <div className="mt-3 flex flex-wrap gap-2">
          {byCategory.map(([label, n]) => (
            <span
              key={label}
              className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-200"
            >
              {label}: {n}
            </span>
          ))}
        </div>
      </div>

      <CoverageImpactAnalytics rows={rows} />

      <section>
        <div className="mb-3 flex items-end justify-between gap-3">
          <div>
            <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Constraint Signatures</div>
            <p className="mt-1 text-sm text-slate-400">
              ~N% of failing patterns (a/b) per held-pin × fan-out signature
            </p>
          </div>
          <div className="rounded-xl border border-primary/30 bg-primary/10 px-3 py-1.5 text-center">
            <div className="text-[10px] uppercase tracking-wide text-primary/80">Signatures</div>
            <div className="font-display text-lg font-semibold text-white">{rows.length}</div>
          </div>
        </div>

        <div className="max-h-[42vh] space-y-2.5 overflow-y-auto pr-1">
          {rows.map((row, idx) => (
            <motion.div
              key={`${row.signature}-${idx}`}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(idx * 0.015, 0.35) }}
              className="rounded-2xl border border-border/50 bg-[#0E1528]/90 p-4"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-lg bg-primary/20 px-2.5 py-1 font-mono text-xs font-semibold text-primary">
                  ~{row.coverageImpactPct ?? 0}%
                </span>
                {row.scope ? (
                  <span className="rounded-lg border border-success/40 bg-success/10 px-2.5 py-1 font-mono text-xs text-success">
                    {row.scope}
                  </span>
                ) : null}
                <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                  {row.constraintCategoryLabel ?? "Constraint"}
                </span>
                <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                  {row.heldPins ?? "—"}
                </span>
                <span className="rounded-lg bg-warning/20 px-2.5 py-1 font-mono text-xs font-semibold text-warning">
                  {row.fanoutSignal ?? "fan-out ?"}
                </span>
                <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                  {row.associatedPatterns ?? 0}/{row.totalFailingPatterns ?? 0} patterns
                </span>
              </div>
              <p className="mt-3 text-[13px] leading-relaxed text-slate-200 sm:text-sm">{row.result}</p>
              {(row.patternLabels?.length ?? 0) > 0 ? (
                <ExpandablePatternIds labels={row.patternLabels ?? []} />
              ) : null}
              <div className="mt-2 text-[11px] text-slate-500">
                example {row.lotId}/{row.dieLabel}
              </div>
            </motion.div>
          ))}
          {rows.length === 0 ? (
            <div className="rounded-2xl border border-border/50 bg-[#0E1528]/90 p-8 text-center text-slate-500">
              No coverage impact signatures detected.
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}

function TimingViolationsCleanLayout({
  diagnosisResults,
}: {
  diagnosisResults: {
    result: string;
    rank?: number;
    lotId?: string;
    dieLabel?: string;
    patternId?: string;
    patternLabel?: string;
    timingChain?: string;
    timingFlop?: string;
    kind?: string;
    classification?: string;
    worstSlackPs?: number;
    setupSlackPs?: number;
    holdSlackPs?: number;
    fastFrequencyMhz?: number;
    slowFrequencyMhz?: number;
    captureEdgeSpacingNs?: number;
    nearMinimumMargin?: boolean;
    fastTimingSet?: string;
    slowTimingSet?: string;
    multiInsertionObserved?: boolean;
  }[];
}) {
  const rows = useMemo(
    () => [...diagnosisResults].sort((a, b) => (a.rank ?? 999) - (b.rank ?? 999)),
    [diagnosisResults],
  );

  const byKind = useMemo(() => {
    const map = new Map<string, number>();
    for (const row of rows) {
      const key = row.kind ? row.kind.charAt(0).toUpperCase() + row.kind.slice(1) : "Timing";
      map.set(key, (map.get(key) ?? 0) + 1);
    }
    return [...map.entries()];
  }, [rows]);

  const sample = rows[0];

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-2 sm:p-4">
      <div className="rounded-2xl border border-primary/30 bg-primary/5 p-4">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Timing Violations</div>
        <p className="mt-2 text-sm text-slate-300">
          Patterns that fail only above a frequency threshold (at-speed / timing-correlated), with STIL
          WaveformTable capture edge spacing as relative margin proxy
        </p>
        <p className="mt-1 text-xs text-slate-500">
          Compare fail logs across timing sets for the same pattern. When only one insertion exists,
          slower set = STIL Period×2 half-rate reference.
        </p>
        {sample ? (
          <p className="mt-3 rounded-xl border border-primary/30 bg-primary/10 px-3 py-2 font-mono text-sm text-primary">
            Fast {sample.fastFrequencyMhz ?? "—"}MHz ({sample.fastTimingSet}) → slow{" "}
            {sample.slowFrequencyMhz ?? "—"}MHz · capture edge spacing{" "}
            {sample.captureEdgeSpacingNs ?? "—"}ns
          </p>
        ) : null}
        <div className="mt-3 flex flex-wrap gap-2">
          {byKind.map(([label, n]) => (
            <span
              key={label}
              className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-200"
            >
              {label}: {n}
            </span>
          ))}
        </div>
      </div>

      <TimingViolationsAnalytics rows={rows} />

      <section>
        <div className="mb-3 flex items-end justify-between gap-3">
          <div>
            <div className="text-[10px] uppercase tracking-[0.16em] text-primary">
              At-Speed Pattern Findings
            </div>
            <p className="mt-1 text-sm text-slate-400">
              Pattern fails only at fast timing set (passes at slower) — STIL edge spacing
            </p>
          </div>
          <div className="rounded-xl border border-primary/30 bg-primary/10 px-3 py-1.5 text-center">
            <div className="text-[10px] uppercase tracking-wide text-primary/80">Findings</div>
            <div className="font-display text-lg font-semibold text-white">{rows.length}</div>
          </div>
        </div>

        <div className="max-h-[42vh] space-y-2.5 overflow-y-auto pr-1">
          {rows.map((row, idx) => (
            <motion.div
              key={`${row.patternLabel}-${row.lotId}-${idx}`}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(idx * 0.015, 0.35) }}
              className="rounded-2xl border border-border/50 bg-[#0E1528]/90 p-4"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-lg bg-primary/20 px-2.5 py-1 font-mono text-xs font-semibold text-primary">
                  {row.patternLabel ?? `P${row.patternId}`}
                </span>
                <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                  {(row.kind ?? "timing").toUpperCase()}
                </span>
                <span className="rounded-lg bg-warning/20 px-2.5 py-1 font-mono text-xs font-semibold text-warning">
                  {row.worstSlackPs ?? "—"} ps
                </span>
                <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                  {row.fastFrequencyMhz ?? "—"}→{row.slowFrequencyMhz ?? "—"} MHz
                </span>
                <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                  spacing {row.captureEdgeSpacingNs ?? "—"}ns
                </span>
                {row.nearMinimumMargin ? (
                  <span className="rounded-lg border border-red-400/40 bg-red-500/10 px-2.5 py-1 font-mono text-xs text-red-300">
                    near min margin
                  </span>
                ) : null}
                <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                  {row.timingChain ?? "chain ?"} / {row.timingFlop ?? "flop ?"}
                </span>
              </div>
              <p className="mt-3 text-[13px] leading-relaxed text-slate-200 sm:text-sm">{row.result}</p>
              <div className="mt-2 text-[11px] text-slate-500">
                {row.lotId}/{row.dieLabel}
                {row.multiInsertionObserved ? " · multi-insertion observed" : " · half-rate STIL reference"}
              </div>
            </motion.div>
          ))}
          {rows.length === 0 ? (
            <div className="rounded-2xl border border-border/50 bg-[#0E1528]/90 p-8 text-center text-slate-500">
              No at-speed timing-correlated pattern fails detected.
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}

function TimingDebugRecsCleanLayout({
  diagnosisResults,
}: {
  diagnosisResults: {
    result: string;
    rank?: number;
    lotId?: string;
    dieLabel?: string;
    patternId?: string;
    patternLabel?: string;
    timingChain?: string;
    timingFlop?: string;
    clockDomain?: string;
    kind?: string;
    classification?: string;
    worstSlackPs?: number;
    historicalMatchCount?: number;
    historicalCite?: string;
    recommendedAction?: string;
    diagnosisTransitionPathDelay?: boolean;
    fastFrequencyMhz?: number;
    captureEdgeSpacingNs?: number;
  }[];
}) {
  const rows = useMemo(
    () => [...diagnosisResults].sort((a, b) => (a.rank ?? 999) - (b.rank ?? 999)),
    [diagnosisResults],
  );

  const byKind = useMemo(() => {
    const map = new Map<string, number>();
    for (const row of rows) {
      const key = row.kind ? row.kind.charAt(0).toUpperCase() + row.kind.slice(1) : "Timing";
      map.set(key, (map.get(key) ?? 0) + 1);
    }
    return [...map.entries()];
  }, [rows]);

  const transitionCount = rows.filter((r) => r.diagnosisTransitionPathDelay).length;

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-2 sm:p-4">
      <div className="rounded-2xl border border-primary/30 bg-primary/5 p-4">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">
          Timing Debug Recommendations
        </div>
        <p className="mt-2 text-sm text-slate-300">
          Review capture clock timing for each pattern&apos;s capture window — names pattern / chain /
          clock domain and cites similar historical frequency fails
        </p>
        <p className="mt-1 text-xs text-slate-500">
          Inputs: Timing Violations evidence + diagnosis transition/path-delay flags + historical cases
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {byKind.map(([label, n]) => (
            <span
              key={label}
              className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-200"
            >
              {label}: {n}
            </span>
          ))}
          <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-200">
            Transition/path-delay: {transitionCount}
          </span>
        </div>
      </div>

      <TimingDebugRecsAnalytics rows={rows} />

      <section>
        <div className="mb-3 flex items-end justify-between gap-3">
          <div>
            <div className="text-[10px] uppercase tracking-[0.16em] text-primary">
              Capture-Window Reviews
            </div>
            <p className="mt-1 text-sm text-slate-400">
              Review capture clock timing for pattern #N&apos;s capture window; N historical cases with
              frequency
            </p>
          </div>
          <div className="rounded-xl border border-primary/30 bg-primary/10 px-3 py-1.5 text-center">
            <div className="text-[10px] uppercase tracking-wide text-primary/80">Recs</div>
            <div className="font-display text-lg font-semibold text-white">{rows.length}</div>
          </div>
        </div>

        <div className="max-h-[42vh] space-y-2.5 overflow-y-auto pr-1">
          {rows.map((row, idx) => (
            <motion.div
              key={`${row.patternLabel}-${row.lotId}-${idx}`}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(idx * 0.015, 0.35) }}
              className="rounded-2xl border border-border/50 bg-[#0E1528]/90 p-4"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-lg bg-primary/20 px-2.5 py-1 font-mono text-xs font-semibold text-primary">
                  {row.patternLabel ?? `P${row.patternId}`}
                </span>
                <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                  {(row.kind ?? "timing").toUpperCase()}
                </span>
                <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                  {row.timingChain ?? "chain ?"}
                </span>
                <span className="rounded-lg bg-warning/20 px-2.5 py-1 font-mono text-xs font-semibold text-warning">
                  {row.clockDomain ?? "domain ?"}
                </span>
                <span className="rounded-lg border border-success/40 bg-success/10 px-2.5 py-1 font-mono text-xs text-success">
                  {row.historicalMatchCount ?? 0} hist
                </span>
                {row.diagnosisTransitionPathDelay ? (
                  <span className="rounded-lg border border-red-400/40 bg-red-500/10 px-2.5 py-1 font-mono text-xs text-red-300">
                    transition/path-delay
                  </span>
                ) : null}
                <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                  {row.recommendedAction ?? "REVIEW_CAPTURE_CLOCK_TIMING"}
                </span>
              </div>
              <p className="mt-3 text-[13px] leading-relaxed text-slate-200 sm:text-sm">{row.result}</p>
              <div className="mt-2 text-[11px] text-slate-500">
                {row.lotId}/{row.dieLabel}
                {row.timingFlop ? ` · ${row.timingFlop}` : ""}
                {row.worstSlackPs != null ? ` · slack ${row.worstSlackPs} ps` : ""}
              </div>
            </motion.div>
          ))}
          {rows.length === 0 ? (
            <div className="rounded-2xl border border-border/50 bg-[#0E1528]/90 p-8 text-center text-slate-500">
              No timing debug recommendations detected.
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}

function WorstSlackCleanLayout({
  diagnosisResults,
}: {
  diagnosisResults: {
    result: string;
    rank?: number;
    lotId?: string;
    dieLabel?: string;
    patternId?: string;
    patternLabel?: string;
    timingChain?: string;
    timingFlop?: string;
    kind?: string;
    worstSlackPs?: number;
    failFrequencyMhz?: number;
    passFrequencyMhz?: number;
    frequencyMarginPct?: number;
  }[];
}) {
  const rows = useMemo(
    () => [...diagnosisResults].sort((a, b) => (a.rank ?? 999) - (b.rank ?? 999)),
    [diagnosisResults],
  );

  const byKind = useMemo(() => {
    const map = new Map<string, number>();
    for (const row of rows) {
      const key = row.kind ? row.kind.charAt(0).toUpperCase() + row.kind.slice(1) : "Timing";
      map.set(key, (map.get(key) ?? 0) + 1);
    }
    return [...map.entries()];
  }, [rows]);

  const top = rows[0];

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-2 sm:p-4">
      <div className="rounded-2xl border border-primary/30 bg-primary/5 p-4">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Worst Slack</div>
        <p className="mt-2 text-sm text-slate-300">
          Fail vs pass timing-set frequencies as a frequency margin proxy; include worst slack (ps) when
          diagnosis provides it
        </p>
        {top ? (
          <p className="mt-3 rounded-xl border border-primary/30 bg-primary/10 px-3 py-2 font-mono text-sm text-primary">
            {top.result}
          </p>
        ) : null}
        <div className="mt-3 flex flex-wrap gap-2">
          {byKind.map(([label, n]) => (
            <span
              key={label}
              className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-200"
            >
              {label}: {n}
            </span>
          ))}
        </div>
      </div>

      <WorstSlackAnalytics rows={rows} />

      <section>
        <div className="mb-3 flex items-end justify-between gap-3">
          <div>
            <div className="text-[10px] uppercase tracking-[0.16em] text-primary">
              Frequency Margin Findings
            </div>
            <p className="mt-1 text-sm text-slate-400">
              Fails at XMHz, passes at YMHz — ~N% frequency margin proxy; worst slack … ps
            </p>
          </div>
          <div className="rounded-xl border border-primary/30 bg-primary/10 px-3 py-1.5 text-center">
            <div className="text-[10px] uppercase tracking-wide text-primary/80">Findings</div>
            <div className="font-display text-lg font-semibold text-white">{rows.length}</div>
          </div>
        </div>

        <div className="max-h-[42vh] space-y-2.5 overflow-y-auto pr-1">
          {rows.map((row, idx) => (
            <motion.div
              key={`${row.patternLabel}-${row.lotId}-${idx}`}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(idx * 0.015, 0.35) }}
              className="rounded-2xl border border-border/50 bg-[#0E1528]/90 p-4"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-lg bg-primary/20 px-2.5 py-1 font-mono text-xs font-semibold text-primary">
                  {row.patternLabel ?? `P${row.patternId}`}
                </span>
                <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                  {(row.kind ?? "timing").toUpperCase()}
                </span>
                <span className="rounded-lg bg-warning/20 px-2.5 py-1 font-mono text-xs font-semibold text-warning">
                  ~{row.frequencyMarginPct ?? "—"}%
                </span>
                {row.worstSlackPs != null ? (
                  <span className="rounded-lg border border-red-400/40 bg-red-500/10 px-2.5 py-1 font-mono text-xs text-red-300">
                    {row.worstSlackPs} ps
                  </span>
                ) : null}
                <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                  {row.failFrequencyMhz ?? "—"}→{row.passFrequencyMhz ?? "—"} MHz
                </span>
                <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                  {row.timingChain ?? "chain ?"} / {row.timingFlop ?? "flop ?"}
                </span>
              </div>
              <p className="mt-3 text-[13px] leading-relaxed text-slate-200 sm:text-sm">{row.result}</p>
              <div className="mt-2 text-[11px] text-slate-500">
                {row.lotId}/{row.dieLabel}
              </div>
            </motion.div>
          ))}
          {rows.length === 0 ? (
            <div className="rounded-2xl border border-border/50 bg-[#0E1528]/90 p-8 text-center text-slate-500">
              No worst-slack / frequency-margin findings detected.
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}

function PowerViolationsCleanLayout({
  diagnosisResults,
  summary,
}: {
  diagnosisResults: {
    result: string;
    rank?: number;
    lotId?: string;
    dieLabel?: string;
    patternId?: string;
    patternLabel?: string;
    irDropMv?: number;
    thermalC?: number;
    status?: string;
    kind?: string;
    flaggedDespitePass?: boolean;
    irThresholdMv?: number;
    thermalThresholdC?: number;
  }[];
  summary?: {
    count?: number;
    totalPatternsInRun?: number;
    flaggedDespitePass?: number;
    byKind?: Record<string, number>;
    irThresholdMv?: number;
    thermalThresholdC?: number;
  };
}) {
  const rows = useMemo(
    () => [...diagnosisResults].sort((a, b) => (a.rank ?? 999) - (b.rank ?? 999)),
    [diagnosisResults],
  );

  const kindLabels: Record<string, string> = {
    ir_drop: "IR Drop",
    thermal: "Thermal",
    both: "IR+Thermal",
  };

  const byKind = useMemo(() => {
    if (summary?.byKind && Object.keys(summary.byKind).length > 0) {
      return Object.entries(summary.byKind)
        .map(([key, n]) => [kindLabels[key] ?? key, Number(n) || 0] as [string, number])
        .filter(([, n]) => n > 0)
        .sort((a, b) => b[1] - a[1]);
    }
    const map = new Map<string, number>();
    for (const row of rows) {
      const key =
        row.kind === "ir_drop"
          ? "IR Drop"
          : row.kind === "thermal"
            ? "Thermal"
            : row.kind === "both"
              ? "IR+Thermal"
              : "Other";
      map.set(key, (map.get(key) ?? 0) + 1);
    }
    return [...map.entries()];
  }, [rows, summary]);

  const displayTotal = summary?.count ?? rows.length;
  const totalPatterns = summary?.totalPatternsInRun ?? 1000;
  const despitePass =
    summary?.flaggedDespitePass ?? rows.filter((r) => r.flaggedDespitePass).length;
  const sample = rows[0];
  const irTh = summary?.irThresholdMv ?? sample?.irThresholdMv ?? 25;
  const thTh = summary?.thermalThresholdC ?? sample?.thermalThresholdC ?? 60;

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-2 sm:p-4">
      <div className="rounded-2xl border border-primary/30 bg-primary/5 p-4">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Power Violations</div>
        <p className="mt-2 text-sm text-slate-300">
          Patterns where IR_DROP_MV or THERMAL_C exceeds threshold — flagged even when STATUS=PASS
        </p>
        <p className="mt-1 text-xs text-slate-500">
          Thresholds: IR &gt; {irTh}mV · Thermal &gt; {thTh}°C · {displayTotal}/{totalPatterns} unique
          patterns · list shows top {rows.length} by severity (PASS-first)
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {byKind.map(([label, n]) => (
            <span
              key={label}
              className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-200"
            >
              {label}: {n}
            </span>
          ))}
          <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-200">
            Despite PASS: {despitePass}
          </span>
        </div>
      </div>

      <PowerViolationsAnalytics rows={rows} summary={summary} />

      <section>
        <div className="mb-3 flex items-end justify-between gap-3">
          <div>
            <div className="text-[10px] uppercase tracking-[0.16em] text-primary">
              IR / Thermal Findings
            </div>
            <p className="mt-1 text-sm text-slate-400">
              Pattern #N: IR_DROP = XmV (threshold 25mV) — flagged despite PASS status
            </p>
          </div>
          <div className="rounded-xl border border-primary/30 bg-primary/10 px-3 py-1.5 text-center">
            <div className="text-[10px] uppercase tracking-wide text-primary/80">Patterns</div>
            <div className="font-display text-lg font-semibold text-white">
              {displayTotal}/{totalPatterns}
            </div>
          </div>
        </div>

        <div className="max-h-[42vh] space-y-2.5 overflow-y-auto pr-1">
          {rows.map((row, idx) => (
            <motion.div
              key={`${row.patternLabel}-${row.lotId}-${row.dieLabel}-${idx}`}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(idx * 0.01, 0.35) }}
              className="rounded-2xl border border-border/50 bg-[#0E1528]/90 p-4"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-lg bg-primary/20 px-2.5 py-1 font-mono text-xs font-semibold text-primary">
                  {row.patternLabel ?? `P${row.patternId}`}
                </span>
                <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                  {(row.kind ?? "power").replace("_", " ").toUpperCase()}
                </span>
                {row.irDropMv != null ? (
                  <span className="rounded-lg bg-warning/20 px-2.5 py-1 font-mono text-xs font-semibold text-warning">
                    IR {row.irDropMv}mV
                  </span>
                ) : null}
                {row.thermalC != null ? (
                  <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                    {row.thermalC}°C
                  </span>
                ) : null}
                {row.flaggedDespitePass ? (
                  <span className="rounded-lg border border-red-400/40 bg-red-500/10 px-2.5 py-1 font-mono text-xs text-red-300">
                    despite PASS
                  </span>
                ) : (
                  <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                    STATUS=FAIL
                  </span>
                )}
              </div>
              <p className="mt-3 text-[13px] leading-relaxed text-slate-200 sm:text-sm">{row.result}</p>
              <div className="mt-2 text-[11px] text-slate-500">
                {row.lotId}/{row.dieLabel}
              </div>
            </motion.div>
          ))}
          {rows.length === 0 ? (
            <div className="rounded-2xl border border-border/50 bg-[#0E1528]/90 p-8 text-center text-slate-500">
              No IR/thermal power violations detected.
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}

function PowerDebugRecsCleanLayout({
  diagnosisResults,
  summary,
}: {
  diagnosisResults: {
    result: string;
    rank?: number;
    lotId?: string;
    dieLabel?: string;
    patternId?: string;
    patternLabel?: string;
    irDropMv?: number;
    thermalC?: number;
    kind?: string;
    pctAboveThreshold?: number;
    flaggedDespitePass?: boolean;
    historicalMatchCount?: number;
    historicalCite?: string;
    recommendedAction?: string;
  }[];
  summary?: { count?: number; workspaceRows?: number };
}) {
  const rows = useMemo(
    () => [...diagnosisResults].sort((a, b) => (a.rank ?? 999) - (b.rank ?? 999)),
    [diagnosisResults],
  );

  const kindLabels: Record<string, string> = {
    ir_drop: "IR Drop",
    thermal: "Thermal",
    both: "IR+Thermal",
  };

  const byKind = useMemo(() => {
    const map = new Map<string, number>();
    for (const row of rows) {
      const key = kindLabels[row.kind ?? ""] ?? (row.kind ? String(row.kind) : "Other");
      map.set(key, (map.get(key) ?? 0) + 1);
    }
    return [...map.entries()].sort((a, b) => b[1] - a[1]);
  }, [rows]);

  const displayTotal = summary?.count ?? rows.length;
  const withHist = rows.filter((r) => (r.historicalMatchCount ?? 0) > 0).length;

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-2 sm:p-4">
      <div className="rounded-2xl border border-primary/30 bg-primary/5 p-4">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">
          Power Debug Recommendations
        </div>
        <p className="mt-2 text-sm text-slate-300">
          Check IR-drop during capture — names pattern, measured value, % above threshold, and cites
          similar historical IR-drop fails within ±5 patterns
        </p>
        <p className="mt-1 text-xs text-slate-500">
          Inputs: Power Violations (IR/thermal) + past IR-drop STATUS=FAIL signatures + historical
          CENTER/NEAR_FULL cases · list shows top {rows.length} of {displayTotal}
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {byKind.map(([label, n]) => (
            <span
              key={label}
              className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-200"
            >
              {label}: {n}
            </span>
          ))}
          <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-200">
            With hist cite: {withHist}
          </span>
        </div>
      </div>

      <PowerDebugRecsAnalytics rows={rows} summary={summary} />

      <section>
        <div className="mb-3 flex items-end justify-between gap-3">
          <div>
            <div className="text-[10px] uppercase tracking-[0.16em] text-primary">
              Capture IR-Drop Checks
            </div>
            <p className="mt-1 text-sm text-slate-400">
              Check IR-drop during capture for Pattern #N (XmV, Y% above threshold); N historical
              cases… — recommend monitoring adjacent patterns
            </p>
          </div>
          <div className="rounded-xl border border-primary/30 bg-primary/10 px-3 py-1.5 text-center">
            <div className="text-[10px] uppercase tracking-wide text-primary/80">Recs</div>
            <div className="font-display text-lg font-semibold text-white">{displayTotal}</div>
          </div>
        </div>

        <div className="max-h-[42vh] space-y-2.5 overflow-y-auto pr-1">
          {rows.map((row, idx) => (
            <motion.div
              key={`${row.patternLabel}-${row.lotId}-${idx}`}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(idx * 0.01, 0.35) }}
              className="rounded-2xl border border-border/50 bg-[#0E1528]/90 p-4"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-lg bg-primary/20 px-2.5 py-1 font-mono text-xs font-semibold text-primary">
                  {row.patternLabel ?? `P${row.patternId}`}
                </span>
                <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                  {(row.kind ?? "ir_drop").replace("_", " ").toUpperCase()}
                </span>
                {row.irDropMv != null ? (
                  <span className="rounded-lg bg-warning/20 px-2.5 py-1 font-mono text-xs font-semibold text-warning">
                    IR {row.irDropMv}mV
                    {row.pctAboveThreshold != null ? ` · +${row.pctAboveThreshold}%` : ""}
                  </span>
                ) : null}
                <span className="rounded-lg border border-success/40 bg-success/10 px-2.5 py-1 font-mono text-xs text-success">
                  {row.historicalMatchCount ?? 0} hist
                </span>
                {row.flaggedDespitePass ? (
                  <span className="rounded-lg border border-red-400/40 bg-red-500/10 px-2.5 py-1 font-mono text-xs text-red-300">
                    despite PASS
                  </span>
                ) : null}
                <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                  {row.recommendedAction ?? "CHECK_IR_DROP_DURING_CAPTURE"}
                </span>
              </div>
              <p className="mt-3 text-[13px] leading-relaxed text-slate-200 sm:text-sm">{row.result}</p>
              <div className="mt-2 text-[11px] text-slate-500">
                {row.lotId}/{row.dieLabel}
                {row.thermalC != null ? ` · ${row.thermalC}°C` : ""}
              </div>
            </motion.div>
          ))}
          {rows.length === 0 ? (
            <div className="rounded-2xl border border-border/50 bg-[#0E1528]/90 p-8 text-center text-slate-500">
              No power debug recommendations detected.
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}

function PeakSwitchingCleanLayout({
  diagnosisResults,
  summary,
}: {
  diagnosisResults: {
    result: string;
    rank?: number;
    lotId?: string;
    dieLabel?: string;
    patternId?: string;
    patternLabel?: string;
    irDropMv?: number;
    avgIrDropMv?: number;
    deltaVsAvgMv?: number;
    isPeak?: boolean;
    thermalC?: number;
    status?: string;
  }[];
  summary?: {
    peakIrDropMv?: number;
    avgIrDropMv?: number;
    patternId?: string;
    patternLabel?: string;
    result?: string;
    kpiValue?: string;
    patternCount?: number;
    deltaVsAvgMv?: number;
  };
}) {
  const rows = useMemo(
    () => [...diagnosisResults].sort((a, b) => (a.rank ?? 999) - (b.rank ?? 999)),
    [diagnosisResults],
  );
  const peakRow = rows.find((r) => r.isPeak) ?? rows[0];
  const hero = summary?.result ?? peakRow?.result;
  const peakMv = summary?.peakIrDropMv ?? peakRow?.irDropMv;
  const avgMv = summary?.avgIrDropMv ?? peakRow?.avgIrDropMv;

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-2 sm:p-4">
      <div className="rounded-2xl border border-primary/30 bg-primary/5 p-4">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Peak Switching</div>
        <p className="mt-2 text-sm text-slate-300">
          MAX(IR_DROP_MV) as switching-activity proxy — electrical downstream of toggle activity
          (no STIL toggle count)
        </p>
        {hero ? (
          <p className="mt-3 rounded-xl border border-primary/30 bg-primary/10 px-3 py-2 font-mono text-sm text-primary">
            {hero}
          </p>
        ) : null}
        <p className="mt-2 text-xs text-slate-500">
          Peak {peakMv != null ? `${peakMv}mV` : "—"} at{" "}
          {summary?.patternLabel ?? peakRow?.patternLabel ?? "?"} · run avg{" "}
          {avgMv != null ? `${avgMv}mV` : "—"} · {summary?.patternCount ?? rows.length} patterns
        </p>
      </div>

      <PeakSwitchingAnalytics rows={rows} summary={summary} />

      <section>
        <div className="mb-3 flex items-end justify-between gap-3">
          <div>
            <div className="text-[10px] uppercase tracking-[0.16em] text-primary">
              Highest IR-Drop Patterns
            </div>
            <p className="mt-1 text-sm text-slate-400">
              Peak IR-drop: XmV at Pattern #N (vs. avg YmV across run)
            </p>
          </div>
          <div className="rounded-xl border border-primary/30 bg-primary/10 px-3 py-1.5 text-center">
            <div className="text-[10px] uppercase tracking-wide text-primary/80">Peak</div>
            <div className="font-display text-lg font-semibold text-white">
              {peakMv != null ? `${peakMv}mV` : "—"}
            </div>
          </div>
        </div>

        <div className="max-h-[42vh] space-y-2.5 overflow-y-auto pr-1">
          {rows.map((row, idx) => (
            <motion.div
              key={`${row.patternLabel}-${row.lotId}-${idx}`}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(idx * 0.01, 0.35) }}
              className="rounded-2xl border border-border/50 bg-[#0E1528]/90 p-4"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-lg bg-primary/20 px-2.5 py-1 font-mono text-xs font-semibold text-primary">
                  {row.patternLabel ?? `P${row.patternId}`}
                </span>
                <span className="rounded-lg bg-warning/20 px-2.5 py-1 font-mono text-xs font-semibold text-warning">
                  IR {row.irDropMv}mV
                </span>
                {row.deltaVsAvgMv != null ? (
                  <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                    {row.deltaVsAvgMv >= 0 ? "+" : ""}
                    {row.deltaVsAvgMv}mV vs avg
                  </span>
                ) : null}
                {row.isPeak ? (
                  <span className="rounded-lg border border-red-400/40 bg-red-500/10 px-2.5 py-1 font-mono text-xs text-red-300">
                    PEAK
                  </span>
                ) : null}
              </div>
              <p className="mt-3 text-[13px] leading-relaxed text-slate-200 sm:text-sm">{row.result}</p>
              <div className="mt-2 text-[11px] text-slate-500">
                {row.lotId}/{row.dieLabel}
              </div>
            </motion.div>
          ))}
          {rows.length === 0 ? (
            <div className="rounded-2xl border border-border/50 bg-[#0E1528]/90 p-8 text-center text-slate-500">
              No peak switching IR data detected.
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}

function DefectSuspectsCleanLayout({
  diagnosisResults,
  summary,
}: {
  diagnosisResults: {
    result: string;
    rank?: number;
    diagnosisRank?: number;
    netId?: string;
    cellName?: string;
    neighborFrom?: string;
    neighborTo?: string;
    chain?: string;
    bitPosition?: number;
    consistentPatterns?: number;
    totalFailingPatterns?: number;
    consistencyRatio?: number;
    confidencePct?: number;
    rootCause?: string;
  }[];
  summary?: {
    count?: number;
    result?: string;
    topNetId?: string;
    topConsistency?: string;
    byRootCause?: Record<string, number>;
    topN?: number;
  };
}) {
  const rows = useMemo(
    () => [...diagnosisResults].sort((a, b) => (a.rank ?? 999) - (b.rank ?? 999)),
    [diagnosisResults],
  );
  const hero = summary?.result;
  const byRoot = useMemo(() => {
    if (summary?.byRootCause) {
      return Object.entries(summary.byRootCause).sort((a, b) => b[1] - a[1]);
    }
    const map = new Map<string, number>();
    for (const row of rows) {
      const key = row.rootCause || "Unknown";
      map.set(key, (map.get(key) ?? 0) + 1);
    }
    return [...map.entries()].sort((a, b) => b[1] - a[1]);
  }, [rows, summary]);

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-2 sm:p-4">
      <div className="rounded-2xl border border-primary/30 bg-primary/5 p-4">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Defect Suspects</div>
        <p className="mt-2 text-sm text-slate-300">
          Top-N diagnosis candidates validated by failing-pattern consistency; cell/net resolved via
          diagnosis + STIL scan order
        </p>
        {hero ? (
          <p className="mt-3 rounded-xl border border-primary/30 bg-primary/10 px-3 py-2 font-mono text-sm text-primary">
            {hero}
          </p>
        ) : null}
        <div className="mt-3 flex flex-wrap gap-2">
          {byRoot.map(([label, n]) => (
            <span
              key={label}
              className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-200"
            >
              {label}: {n}
            </span>
          ))}
        </div>
      </div>

      <DefectSuspectsAnalytics rows={rows} summary={summary} />

      <section>
        <div className="mb-3 flex items-end justify-between gap-3">
          <div>
            <div className="text-[10px] uppercase tracking-[0.16em] text-primary">
              Ranked Net Suspects
            </div>
            <p className="mt-1 text-sm text-slate-400">
              Net N#### (Ua→Ub) — diagnosis rank 1, consistent with C/T failing patterns
            </p>
          </div>
          <div className="rounded-xl border border-primary/30 bg-primary/10 px-3 py-1.5 text-center">
            <div className="text-[10px] uppercase tracking-wide text-primary/80">Suspects</div>
            <div className="font-display text-lg font-semibold text-white">
              {summary?.count ?? rows.length}
            </div>
          </div>
        </div>

        <div className="max-h-[42vh] space-y-2.5 overflow-y-auto pr-1">
          {rows.map((row, idx) => (
            <motion.div
              key={`${row.netId}-${row.diagnosisRank}-${idx}`}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(idx * 0.01, 0.35) }}
              className="rounded-2xl border border-border/50 bg-[#0E1528]/90 p-4"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-lg bg-primary/20 px-2.5 py-1 font-mono text-xs font-semibold text-primary">
                  {row.netId ?? "N?"}
                </span>
                <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                  rank {row.diagnosisRank ?? row.rank}
                </span>
                <span className="rounded-lg bg-warning/20 px-2.5 py-1 font-mono text-xs font-semibold text-warning">
                  {row.consistentPatterns}/{row.totalFailingPatterns} patterns
                </span>
                {row.rootCause ? (
                  <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                    {row.rootCause}
                  </span>
                ) : null}
                {row.confidencePct != null ? (
                  <span className="rounded-lg border border-success/40 bg-success/10 px-2.5 py-1 font-mono text-xs text-success">
                    {row.confidencePct}%
                  </span>
                ) : null}
              </div>
              <p className="mt-3 text-[13px] leading-relaxed text-slate-200 sm:text-sm">{row.result}</p>
              <div className="mt-2 text-[11px] text-slate-500">
                {row.chain ?? "chain?"}
                {row.bitPosition != null ? ` · bit ${row.bitPosition}` : ""}
                {row.cellName ? ` · ${row.cellName}` : ""}
                {row.neighborFrom && row.neighborTo
                  ? ` · ${row.neighborFrom}→${row.neighborTo}`
                  : ""}
              </div>
            </motion.div>
          ))}
          {rows.length === 0 ? (
            <div className="rounded-2xl border border-border/50 bg-[#0E1528]/90 p-8 text-center text-slate-500">
              No defect suspects detected.
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}

function InvestigationRecsCleanLayout({
  diagnosisResults,
  summary,
}: {
  diagnosisResults: {
    result: string;
    rank?: number;
    diagnosisRank?: number;
    netId?: string;
    cellName?: string;
    neighborFrom?: string;
    neighborTo?: string;
    chain?: string;
    faultHypothesis?: string;
    transitionFaultCount?: number;
    irDropMv?: number;
    irThresholdMv?: number;
    powerInducedRuledOut?: boolean;
    historicalMatchCount?: number;
    pfaTechnique?: string;
    rootCause?: string;
  }[];
  summary?: {
    count?: number;
    result?: string;
    transitionFaultCount?: number;
    irDropMv?: number;
    irThresholdMv?: number;
    powerInducedRuledOut?: boolean;
    ruledOutCount?: number;
    byFaultHypothesis?: Record<string, number>;
  };
}) {
  const rows = useMemo(
    () => [...diagnosisResults].sort((a, b) => (a.rank ?? 999) - (b.rank ?? 999)),
    [diagnosisResults],
  );
  const hero = summary?.result ?? rows[0]?.result;
  const byHyp = useMemo(() => {
    if (summary?.byFaultHypothesis) {
      return Object.entries(summary.byFaultHypothesis).sort((a, b) => b[1] - a[1]);
    }
    const map = new Map<string, number>();
    for (const row of rows) {
      const key = row.faultHypothesis || "Unknown";
      map.set(key, (map.get(key) ?? 0) + 1);
    }
    return [...map.entries()].sort((a, b) => b[1] - a[1]);
  }, [rows, summary]);

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-2 sm:p-4">
      <div className="rounded-2xl border border-primary/30 bg-primary/5 p-4">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">
          Investigation Recommendations
        </div>
        <p className="mt-2 text-sm text-slate-300">
          Investigate top defect-suspect nets — confirm not power-induced via TF/IR cross-check,
          cite fault hypothesis, recommend PFA from historical precedent
        </p>
        {hero ? (
          <p className="mt-3 rounded-xl border border-primary/30 bg-primary/10 px-3 py-2 font-mono text-[13px] leading-relaxed text-primary">
            {hero}
          </p>
        ) : null}
        <p className="mt-2 text-xs text-slate-500">
          Cross-check: TF count={summary?.transitionFaultCount ?? "—"} · IR{" "}
          {summary?.irDropMv != null ? `${summary.irDropMv}mV` : "—"} (threshold{" "}
          {summary?.irThresholdMv ?? 15}mV)
          {summary?.powerInducedRuledOut ? " · power false-fail ruled out" : ""}
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {byHyp.map(([label, n]) => (
            <span
              key={label}
              className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-200"
            >
              {label}: {n}
            </span>
          ))}
        </div>
      </div>

      <InvestigationRecsAnalytics rows={rows} summary={summary} />

      <section>
        <div className="mb-3 flex items-end justify-between gap-3">
          <div>
            <div className="text-[10px] uppercase tracking-[0.16em] text-primary">
              PFA Investigation Paths
            </div>
            <p className="mt-1 text-sm text-slate-400">
              Investigate Net N#### — suspected bridging; TF/IR cross-check; historical PFA cite
            </p>
          </div>
          <div className="rounded-xl border border-primary/30 bg-primary/10 px-3 py-1.5 text-center">
            <div className="text-[10px] uppercase tracking-wide text-primary/80">Recs</div>
            <div className="font-display text-lg font-semibold text-white">
              {summary?.count ?? rows.length}
            </div>
          </div>
        </div>

        <div className="max-h-[42vh] space-y-2.5 overflow-y-auto pr-1">
          {rows.map((row, idx) => (
            <motion.div
              key={`${row.netId}-${row.rank}-${idx}`}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(idx * 0.01, 0.35) }}
              className="rounded-2xl border border-border/50 bg-[#0E1528]/90 p-4"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-lg bg-primary/20 px-2.5 py-1 font-mono text-xs font-semibold text-primary">
                  {row.netId ?? "N?"}
                </span>
                <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                  {row.faultHypothesis ?? "fault?"}
                </span>
                <span className="rounded-lg bg-warning/20 px-2.5 py-1 font-mono text-xs font-semibold text-warning">
                  TF={row.transitionFaultCount ?? 0} · IR {row.irDropMv ?? "?"}mV
                </span>
                {row.powerInducedRuledOut ? (
                  <span className="rounded-lg border border-success/40 bg-success/10 px-2.5 py-1 font-mono text-xs text-success">
                    real defect
                  </span>
                ) : (
                  <span className="rounded-lg border border-red-400/40 bg-red-500/10 px-2.5 py-1 font-mono text-xs text-red-300">
                    verify power
                  </span>
                )}
                <span className="rounded-lg border border-success/40 bg-success/10 px-2.5 py-1 font-mono text-xs text-success">
                  {row.historicalMatchCount ?? 0} hist
                </span>
                {row.pfaTechnique ? (
                  <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                    {row.pfaTechnique}
                  </span>
                ) : null}
              </div>
              <p className="mt-3 text-[13px] leading-relaxed text-slate-200 sm:text-sm">{row.result}</p>
              <div className="mt-2 text-[11px] text-slate-500">
                {row.chain ?? "chain?"}
                {row.cellName ? ` · ${row.cellName}` : ""}
                {row.neighborFrom && row.neighborTo
                  ? ` · ${row.neighborFrom}→${row.neighborTo}`
                  : ""}
              </div>
            </motion.div>
          ))}
          {rows.length === 0 ? (
            <div className="rounded-2xl border border-border/50 bg-[#0E1528]/90 p-8 text-center text-slate-500">
              No investigation recommendations detected.
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}

function DefectLocalizationCleanLayout({
  diagnosisResults,
  summary,
}: {
  diagnosisResults: {
    result: string;
    rank?: number;
    netId?: string;
    cellName?: string;
    neighborFrom?: string;
    neighborTo?: string;
    chain?: string;
    confidencePct?: number;
    consistencyRatio?: number;
    consistentPatterns?: number;
    totalFailingPatterns?: number;
    historicalMatchCount?: number;
    dieLocalXUm?: number;
    dieLocalYUm?: number;
    waferX?: number;
    waferY?: number;
    debugPriority?: string;
    xyAvailable?: boolean;
    powerInducedRuledOut?: boolean;
    faultHypothesis?: string;
  }[];
  summary?: {
    count?: number;
    kpiValue?: string;
    averageConfidencePct?: number;
    result?: string;
    topNetId?: string;
    topConfidencePct?: number;
    xyAvailableCount?: number;
    byPriority?: Record<string, number>;
  };
}) {
  const rows = useMemo(
    () => [...diagnosisResults].sort((a, b) => (a.rank ?? 999) - (b.rank ?? 999)),
    [diagnosisResults],
  );
  const hero = summary?.result ?? rows[0]?.result;
  const avg = summary?.kpiValue ?? (summary?.averageConfidencePct != null ? `${summary.averageConfidencePct}%` : "—");

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-2 sm:p-4">
      <div className="rounded-2xl border border-primary/30 bg-primary/5 p-4">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Defect Localization</div>
        <p className="mt-2 text-sm text-slate-300">
          Localization confidence % from analyzed defect-suspect / investigation recommendations,
          FR-009 die-local &amp; wafer XY, and historical PFA precedent
        </p>
        {hero ? (
          <p className="mt-3 rounded-xl border border-primary/30 bg-primary/10 px-3 py-2 font-mono text-[13px] leading-relaxed text-primary">
            {hero}
          </p>
        ) : null}
        <p className="mt-2 text-xs text-slate-500">
          Average confidence {avg} · {summary?.xyAvailableCount ?? rows.filter((r) => r.xyAvailable).length}/
          {summary?.count ?? rows.length} with XY · top {summary?.topNetId ?? rows[0]?.netId ?? "—"}
        </p>
      </div>

      <DefectLocalizationAnalytics rows={rows} summary={summary} />

      <section>
        <div className="mb-3 flex items-end justify-between gap-3">
          <div>
            <div className="text-[10px] uppercase tracking-[0.16em] text-primary">
              Localized Suspect Nets
            </div>
            <p className="mt-1 text-sm text-slate-400">
              Defect localization confidence: NN% — Net N#### at wafer (x,y), rank, consistency, PFA
            </p>
          </div>
          <div className="rounded-xl border border-primary/30 bg-primary/10 px-3 py-1.5 text-center">
            <div className="text-[10px] uppercase tracking-wide text-primary/80">Avg Conf</div>
            <div className="font-display text-lg font-semibold text-white">{avg}</div>
          </div>
        </div>

        <div className="max-h-[42vh] space-y-2.5 overflow-y-auto pr-1">
          {rows.map((row, idx) => (
            <motion.div
              key={`${row.netId}-${row.rank}-${idx}`}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(idx * 0.01, 0.35) }}
              className="rounded-2xl border border-border/50 bg-[#0E1528]/90 p-4"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-lg bg-primary/20 px-2.5 py-1 font-mono text-xs font-semibold text-primary">
                  {row.netId ?? "N?"}
                </span>
                <span className="rounded-lg bg-warning/20 px-2.5 py-1 font-mono text-xs font-semibold text-warning">
                  {row.confidencePct ?? "—"}%
                </span>
                {row.debugPriority ? (
                  <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                    {row.debugPriority}
                  </span>
                ) : null}
                {row.xyAvailable ? (
                  <span className="rounded-lg border border-success/40 bg-success/10 px-2.5 py-1 font-mono text-xs text-success">
                    XY
                  </span>
                ) : null}
                <span className="rounded-lg border border-border/60 bg-white/5 px-2.5 py-1 font-mono text-xs text-slate-300">
                  {row.consistentPatterns}/{row.totalFailingPatterns} · {row.historicalMatchCount ?? 0}{" "}
                  hist
                </span>
              </div>
              <p className="mt-3 text-[13px] leading-relaxed text-slate-200 sm:text-sm">{row.result}</p>
              <div className="mt-2 text-[11px] text-slate-500">
                {row.chain ?? "chain?"}
                {row.waferX != null && row.waferY != null
                  ? ` · wafer (${Number(row.waferX).toFixed(1)}, ${Number(row.waferY).toFixed(1)})`
                  : ""}
                {row.dieLocalXUm != null && row.dieLocalYUm != null
                  ? ` · die (${Number(row.dieLocalXUm).toFixed(1)}µm, ${Number(row.dieLocalYUm).toFixed(1)}µm)`
                  : ""}
              </div>
            </motion.div>
          ))}
          {rows.length === 0 ? (
            <div className="rounded-2xl border border-border/50 bg-[#0E1528]/90 p-8 text-center text-slate-500">
              No defect localization results detected.
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}

export function KpiDrillDownWorkspace({
  kpiId,
  onClose,
}: {
  kpiId: ScanDebugKpiId;
  onClose: () => void;
}) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["kpi-workspace", kpiId],
    queryFn: () => fetchKpiWorkspace(kpiId),
    retry: 1,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
    placeholderData: (previous) => previous,
  });
  const [copilotInput, setCopilotInput] = useState("");
  const [messages, setMessages] = useState<{ role: "user" | "assistant"; content: string }[]>([]);

  const toast = (action: string) => {
    setMessages((m) => [
      ...m,
      { role: "assistant", content: `Action recorded: ${action} for ${data?.title ?? kpiId}.` },
    ]);
  };

  const starters = useMemo(() => data?.copilotStarters ?? [], [data]);
  const isBrokenChainsClean =
    kpiId === "broken_chains" || data?.layout === "broken_chains_clean";
  const isScanChainRecsClean =
    kpiId === "debug_recommendations" || data?.layout === "scan_chain_recs_clean";
  const isScanChainConfidenceClean =
    kpiId === "avg_ai_confidence" || data?.layout === "scan_chain_confidence_clean";
  const isConstraintViolationsClean =
    kpiId === "constraint_violations" || data?.layout === "constraint_violations_clean";
  const isConstraintReviewRecsClean =
    kpiId === "pending_review" || data?.layout === "constraint_review_recs_clean";
  const isCoverageImpactClean =
    kpiId === "coverage_impact" || data?.layout === "coverage_impact_clean";
  const isTimingViolationsClean =
    kpiId === "timing_violations" || data?.layout === "timing_violations_clean";
  const isTimingDebugRecsClean =
    kpiId === "timing_debug_recs" || data?.layout === "timing_debug_recs_clean";
  const isWorstSlackClean = kpiId === "worst_slack" || data?.layout === "worst_slack_clean";
  const isPowerViolationsClean =
    kpiId === "power_violations" || data?.layout === "power_violations_clean";
  const isPowerDebugRecsClean =
    kpiId === "power_debug_recs" || data?.layout === "power_debug_recs_clean";
  const isPeakSwitchingClean =
    kpiId === "peak_switching" || data?.layout === "peak_switching_clean";
  const isDefectSuspectsClean =
    kpiId === "defect_suspects" || data?.layout === "defect_suspects_clean";
  const isInvestigationRecsClean =
    kpiId === "investigation_recs" || data?.layout === "investigation_recs_clean";
  const isDefectLocalizationClean =
    kpiId === "defect_localization" || data?.layout === "defect_localization_clean";

  return (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-3 backdrop-blur-sm"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.96, y: 12 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          className="flex h-[92vh] w-[95vw] flex-col overflow-hidden rounded-glass border border-border bg-[#0B1020] shadow-2xl"
        >
          <div className="flex items-center justify-between border-b border-border/70 px-5 py-3">
            <h2 className="font-display text-xl font-semibold text-white">
              {data?.title ?? "Loading…"}
            </h2>
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl border border-border p-2 text-slate-300 hover:bg-white/5"
              aria-label="Close"
            >
              <X size={18} />
            </button>
          </div>

          {isLoading ? (
            <div className="grid flex-1 place-items-center text-muted">
              Loading workspace…
              {kpiId === "avg_ai_confidence" ? (
                <div className="mt-2 text-xs text-slate-500">Scoring confidence across all dies (may take up to a minute)</div>
              ) : null}
            </div>
          ) : error ? (
            <div className="grid flex-1 place-items-center p-6 text-center">
              <p className="text-sm text-warning">Failed to load KPI workspace.</p>
              <p className="mt-2 text-xs text-slate-500">{error.message}</p>
            </div>
          ) : !data ? (
            <div className="grid flex-1 place-items-center text-muted">No workspace data.</div>
          ) : isBrokenChainsClean ? (
            <div className="flex-1 overflow-y-auto p-4">
              <BrokenChainsCleanLayout
                diagnosisResults={data.diagnosisResults ?? []}
              />
            </div>
          ) : isScanChainRecsClean ? (
            <div className="flex-1 overflow-y-auto p-4">
              <ScanChainRecsCleanLayout diagnosisResults={data.diagnosisResults ?? []} />
            </div>
          ) : isScanChainConfidenceClean ? (
            <div className="flex-1 overflow-y-auto p-4">
              <ScanChainConfidenceCleanLayout diagnosisResults={data.diagnosisResults ?? []} />
            </div>
          ) : isConstraintViolationsClean ? (
            <div className="flex-1 overflow-y-auto p-4">
              <ConstraintViolationsCleanLayout diagnosisResults={data.diagnosisResults ?? []} />
            </div>
          ) : isConstraintReviewRecsClean ? (
            <div className="flex-1 overflow-y-auto p-4">
              <ConstraintReviewRecsCleanLayout diagnosisResults={data.diagnosisResults ?? []} />
            </div>
          ) : isCoverageImpactClean ? (
            <div className="flex-1 overflow-y-auto p-4">
              <CoverageImpactCleanLayout diagnosisResults={data.diagnosisResults ?? []} />
            </div>
          ) : isTimingViolationsClean ? (
            <div className="flex-1 overflow-y-auto p-4">
              <TimingViolationsCleanLayout diagnosisResults={data.diagnosisResults ?? []} />
            </div>
          ) : isTimingDebugRecsClean ? (
            <div className="flex-1 overflow-y-auto p-4">
              <TimingDebugRecsCleanLayout diagnosisResults={data.diagnosisResults ?? []} />
            </div>
          ) : isWorstSlackClean ? (
            <div className="flex-1 overflow-y-auto p-4">
              <WorstSlackCleanLayout diagnosisResults={data.diagnosisResults ?? []} />
            </div>
          ) : isPowerViolationsClean ? (
            <div className="flex-1 overflow-y-auto p-4">
              <PowerViolationsCleanLayout
                diagnosisResults={data.diagnosisResults ?? []}
                summary={data.powerViolationSummary}
              />
            </div>
          ) : isPowerDebugRecsClean ? (
            <div className="flex-1 overflow-y-auto p-4">
              <PowerDebugRecsCleanLayout
                diagnosisResults={data.diagnosisResults ?? []}
                summary={data.powerDebugRecSummary}
              />
            </div>
          ) : isPeakSwitchingClean ? (
            <div className="flex-1 overflow-y-auto p-4">
              <PeakSwitchingCleanLayout
                diagnosisResults={data.diagnosisResults ?? []}
                summary={data.peakSwitchingSummary}
              />
            </div>
          ) : isDefectSuspectsClean ? (
            <div className="flex-1 overflow-y-auto p-4">
              <DefectSuspectsCleanLayout
                diagnosisResults={data.diagnosisResults ?? []}
                summary={data.defectSuspectSummary}
              />
            </div>
          ) : isInvestigationRecsClean ? (
            <div className="flex-1 overflow-y-auto p-4">
              <InvestigationRecsCleanLayout
                diagnosisResults={data.diagnosisResults ?? []}
                summary={data.investigationRecSummary}
              />
            </div>
          ) : isDefectLocalizationClean ? (
            <div className="flex-1 overflow-y-auto p-4">
              <DefectLocalizationCleanLayout
                diagnosisResults={data.diagnosisResults ?? []}
                summary={data.defectLocalizationSummary}
              />
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto p-4">
              <div className="mb-4 grid grid-cols-2 gap-2 md:grid-cols-4 xl:grid-cols-6">
                {data.summaryCards.map((c, idx) => (
                  <div key={`${c.label}-${idx}`} className="rounded-xl border border-border/70 bg-white/5 p-3">
                    <div className="text-[10px] uppercase tracking-wide text-slate-400">{c.label}</div>
                    <div className="mt-1 text-sm font-medium text-white">{c.value}</div>
                  </div>
                ))}
              </div>

              <div className="mb-4 grid h-[420px] grid-cols-1 overflow-hidden rounded-glass border border-border/70 lg:grid-cols-[40%_60%]">
                <div className="border-b border-border/70 lg:border-b-0 lg:border-r">
                  <KpiScanDebugDecisionPanel decision={data.decision} onAction={toast} />
                </div>
                <div className="p-4">
                  <VizPanel type={data.visualizationType} series={data.vizSeries} />
                </div>
              </div>

              <div className="mb-4 grid grid-cols-1 gap-3 lg:grid-cols-2">
                <div className="glass-card p-4">
                  <h3 className="mb-3 text-sm font-medium text-white">Engineering Breakdown</h3>
                  <div className="space-y-2">
                    {data.breakdown.map((b, idx) => (
                      <div key={`${b.dimension}-${b.value}-${idx}`} className="flex items-center gap-3 text-sm">
                        <span className="w-28 text-slate-400">{b.dimension}</span>
                        <span className="flex-1 text-slate-200">{b.value}</span>
                        <span className="text-primary">{b.share}%</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="glass-card p-4">
                  <h3 className="mb-3 text-sm font-medium text-white">Engineering Impact</h3>
                  <div className="overflow-x-auto">
                    <table className="min-w-full text-sm">
                      <thead className="text-[11px] uppercase text-slate-400">
                        <tr>
                          <th className="py-1 text-left">Metric</th>
                          <th className="py-1 text-left">Before</th>
                          <th className="py-1 text-left">After</th>
                          <th className="py-1 text-left">Delta</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.impact.map((m) => (
                          <tr key={m.label} className="border-t border-border/40">
                            <td className="py-2 text-slate-200">{m.label}</td>
                            <td className="py-2 text-slate-400">{m.before}</td>
                            <td className="py-2 text-slate-200">{m.after}</td>
                            <td className="py-2 text-success">{m.delta}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>

              <div className="mb-4 flex flex-wrap gap-2">
                {["Approve", "Reject", "Modify", "Assign"].map((a) => (
                  <button
                    key={a}
                    type="button"
                    onClick={() => toast(a)}
                    className="rounded-xl border border-border bg-primary/15 px-3 py-2 text-sm text-white hover:bg-primary/25"
                  >
                    {a}
                  </button>
                ))}
              </div>

              <div className="glass-card p-4">
                <h3 className="mb-3 text-sm font-medium text-white">AI Copilot</h3>
                <div className="mb-3 flex flex-wrap gap-2">
                  {starters.map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => {
                        setMessages((m) => [
                          ...m,
                          { role: "user", content: s },
                          {
                            role: "assistant",
                            content: `${data.decision.whyAiRecommended} For “${s}”: ${data.decision.whatImproves}`,
                          },
                        ]);
                      }}
                      className="rounded-full border border-border/80 bg-white/5 px-3 py-1 text-xs text-slate-300 hover:border-primary/40"
                    >
                      {s}
                    </button>
                  ))}
                </div>
                {messages.length > 0 ? (
                  <div className="mb-3 max-h-32 space-y-1 overflow-y-auto rounded-xl border border-border/60 bg-black/20 p-3 text-sm text-slate-300">
                    {messages.map((m, i) => (
                      <div key={`${m.role}-${i}`}>{m.content}</div>
                    ))}
                  </div>
                ) : null}
                <form
                  className="flex gap-2"
                  onSubmit={(e) => {
                    e.preventDefault();
                    if (!copilotInput.trim()) return;
                    const q = copilotInput.trim();
                    setCopilotInput("");
                    setMessages((m) => [
                      ...m,
                      { role: "user", content: q },
                      {
                        role: "assistant",
                        content: `Based on ${data.title}: ${data.decision.shouldApprove}`,
                      },
                    ]);
                  }}
                >
                  <input
                    value={copilotInput}
                    onChange={(e) => setCopilotInput(e.target.value)}
                    placeholder="Ask the Scan Debug agent…"
                    className="flex-1 rounded-xl border border-border bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-primary/50"
                  />
                  <button
                    type="submit"
                    className="rounded-xl bg-primary px-4 py-2 text-sm font-medium text-white"
                  >
                    Ask
                  </button>
                </form>
              </div>
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
