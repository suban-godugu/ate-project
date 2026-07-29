"use client";

import { Eraser, FileDown, Wifi, WifiOff } from "lucide-react";
import { useAnalysis } from "@/wafervision/hooks/useAnalysis";
import { exportRows } from "@/wafervision/utils/batchAggregates";
import { downloadCsv, downloadJson, timestampStamp } from "@/wafervision/utils/export";
import { cn } from "@/wafervision/utils/format";

/** Compact session bar — grid / export / clear (upload lives in header). */
export function WaferSessionBar() {
  const {
    files,
    gridMode,
    setGridMode,
    gridSize,
    setGridSize,
    isAnalyzing,
    results,
    clearSession,
    connectionStatus,
  } = useAnalysis();

  const canExport = results.length > 0 && !isAnalyzing;
  const canClear = (results.length > 0 || files.length > 0) && !isAnalyzing;

  const statusChip =
    isAnalyzing
      ? { label: "Analyzing…", icon: Wifi, className: "border-[#7C3AED]/50 text-[#A78BFA]" }
      : connectionStatus === "connected"
        ? { label: "API Connected", icon: Wifi, className: "border-emerald-500/40 text-emerald-400" }
        : connectionStatus === "offline"
          ? { label: "API Offline", icon: WifiOff, className: "border-red-500/40 text-red-400" }
          : connectionStatus === "backend_error"
            ? { label: "Backend Error", icon: WifiOff, className: "border-red-500/40 text-red-400" }
            : { label: "API Idle", icon: Wifi, className: "border-[#2D3748] text-slate-400" };

  const StatusIcon = statusChip.icon;

  const exportCsv = () => {
    const rows = exportRows(results);
    const stamp = timestampStamp();
    downloadCsv(
      `wafervision-batch-${stamp}.csv`,
      [
        "Wafer Name",
        "Defect",
        "LOT",
        "Yield",
        "Confidence",
        "Good Dies",
        "Fail Dies",
        "Total Dies",
      ],
      rows.map((r) => [
        r.waferName,
        r.defect,
        r.lot,
        r.yield,
        r.confidence,
        r.goodDies,
        r.failDies,
        r.totalDies,
      ])
    );
  };

  const exportJson = () => {
    const stamp = timestampStamp();
    downloadJson(`wafervision-batch-${stamp}.json`, {
      exported_at: new Date().toISOString(),
      wafer_count: results.length,
      wafers: exportRows(results),
      spatial: results.map((r) => ({
        name: r.source_file || r.wafer_id,
        spatial_analysis: r.spatial_analysis ?? null,
      })),
    });
  };

  return (
    <section className="panel flex flex-wrap items-center gap-2 p-3">
      <span className="font-mono text-xs text-slate-400">
        {results.length} analyzed · {files.length} queued
      </span>
      <span
        className={cn(
          "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs",
          statusChip.className
        )}
      >
        <StatusIcon className="h-3.5 w-3.5" />
        {statusChip.label}
      </span>

      <div className="mx-1 hidden h-6 w-px bg-[#2D3748] sm:block" />

      <fieldset disabled={isAnalyzing} className="flex flex-wrap items-center gap-2 disabled:opacity-60">
        {(["automatic", "manual"] as const).map((mode) => (
          <label
            key={mode}
            className={cn(
              "cursor-pointer rounded-lg border px-2.5 py-1.5 text-xs capitalize transition",
              gridMode === mode
                ? "border-[#7C3AED] bg-[#7C3AED]/20 text-white"
                : "border-[#2D3748] text-slate-400 hover:border-[#7C3AED]/50"
            )}
          >
            <input
              type="radio"
              name="session-grid-mode"
              className="sr-only"
              checked={gridMode === mode}
              onChange={() => setGridMode(mode)}
            />
            {mode === "automatic" ? "Automatic Grid" : "Manual Grid"}
          </label>
        ))}
        {gridMode === "manual" && (
          <input
            type="number"
            min={2}
            max={256}
            value={gridSize}
            disabled={isAnalyzing}
            onChange={(e) => {
              const n = Number(e.target.value);
              setGridSize(n ? Math.min(256, Math.max(2, n)) : 2);
            }}
            className="h-8 w-16 rounded-lg border border-[#2D3748] bg-transparent px-2 text-xs text-white focus:border-[#7C3AED]"
            aria-label="Manual grid size"
          />
        )}
      </fieldset>

      <div className="ml-auto flex flex-wrap items-center gap-2">
        <button
          type="button"
          disabled={!canExport}
          onClick={exportCsv}
          className="inline-flex items-center gap-1.5 rounded-lg border border-[#2D3748] px-2.5 py-1.5 text-xs text-slate-200 hover:border-[#7C3AED]/50 disabled:opacity-40"
        >
          <FileDown className="h-3.5 w-3.5" />
          CSV
        </button>
        <button
          type="button"
          disabled={!canExport}
          onClick={exportJson}
          className="inline-flex items-center gap-1.5 rounded-lg border border-[#2D3748] px-2.5 py-1.5 text-xs text-slate-200 hover:border-[#7C3AED]/50 disabled:opacity-40"
        >
          <FileDown className="h-3.5 w-3.5" />
          JSON
        </button>
        <button
          type="button"
          disabled
          title="PDF export planned for a later release."
          className="inline-flex cursor-not-allowed items-center gap-1.5 rounded-lg border border-[#2D3748] px-2.5 py-1.5 text-xs text-slate-400 opacity-40"
        >
          <FileDown className="h-3.5 w-3.5" />
          PDF
        </button>
        <button
          type="button"
          disabled={!canClear}
          onClick={clearSession}
          className="inline-flex items-center gap-1.5 rounded-lg border border-red-500/40 bg-red-500/10 px-2.5 py-1.5 text-xs text-red-400 disabled:opacity-40"
        >
          <Eraser className="h-3.5 w-3.5" />
          Clear All
        </button>
      </div>
    </section>
  );
}
