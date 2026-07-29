"use client";

import { Eraser, FileJson, FileSpreadsheet, FileText, Play } from "lucide-react";

import { useAnalysis } from "@/hooks/useAnalysis";
import { buildExportRows } from "@/utils/batchAggregates";
import {
  exportSessionCsv,
  exportSessionJson,
} from "@/utils/export";

/** Page-top session actions (formerly the left Session panel). */
export function SessionToolbar() {
  const { results, clearSession, files, isAnalyzing, analyze } = useAnalysis();

  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <p className="text-xs text-[var(--muted)]">
        {results.length} analyzed · {files.length} queued
      </p>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          disabled={isAnalyzing || files.length === 0}
          onClick={analyze}
          className="inline-flex items-center gap-1.5 rounded-lg bg-ink-800 px-3 py-2 text-xs font-semibold text-white transition hover:bg-ink-700 disabled:cursor-not-allowed disabled:opacity-40 dark:bg-ink-200 dark:text-ink-950 dark:hover:bg-white"
        >
          <Play className="h-3.5 w-3.5" />
          {isAnalyzing ? "Analyzing…" : "Analyze Wafer"}
        </button>
        <button
          type="button"
          disabled={!results.length || isAnalyzing}
          onClick={() => exportSessionCsv(buildExportRows(results))}
          className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--line)] px-3 py-2 text-xs font-medium disabled:opacity-40"
        >
          <FileSpreadsheet className="h-3.5 w-3.5" />
          CSV
        </button>
        <button
          type="button"
          disabled={!results.length || isAnalyzing}
          onClick={() =>
            exportSessionJson({
              exported_at: new Date().toISOString(),
              wafer_count: results.length,
              wafers: buildExportRows(results),
              // Spatial + LOT fields copied from API responses (no client recalculation)
              spatial: results.map((r) => ({
                wafer: r.source_file || r.wafer_id,
                spatial_analysis: r.spatial_analysis ?? null,
              })),
            })
          }
          className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--line)] px-3 py-2 text-xs font-medium disabled:opacity-40"
        >
          <FileJson className="h-3.5 w-3.5" />
          JSON
        </button>
        <button
          type="button"
          disabled
          title="PDF export planned for a later release"
          className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--line)] px-3 py-2 text-xs font-medium opacity-40"
        >
          <FileText className="h-3.5 w-3.5" />
          PDF
        </button>
        <button
          type="button"
          disabled={(!results.length && !files.length) || isAnalyzing}
          onClick={clearSession}
          className="inline-flex items-center gap-1.5 rounded-lg border border-signal-fail/40 bg-signal-fail/10 px-3 py-2 text-xs font-semibold text-signal-fail disabled:opacity-40"
        >
          <Eraser className="h-3.5 w-3.5" />
          Clear All
        </button>
      </div>
    </div>
  );
}
