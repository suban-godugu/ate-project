"use client";

import {
  Eraser,
  FileJson,
  FileSpreadsheet,
  FileText,
  FolderOpen,
  Play,
  UploadCloud,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { useAnalysis } from "@/wafervision/hooks/useAnalysis";
import { exportRows } from "@/wafervision/utils/batchAggregates";
import { downloadCsv, downloadJson, timestampStamp } from "@/wafervision/utils/export";
import { cn } from "@/wafervision/utils/format";

const ACCEPTED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp"] as const;

function isAccepted(file: File): boolean {
  const lower = file.name.toLowerCase();
  return ACCEPTED_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

/** Agent-style workspace ribbon: upload, grid, analyze, export. */
export function ControlRibbon() {
  const {
    files,
    setFiles,
    results,
    clearSession,
    isAnalyzing,
    analyze,
    gridMode,
    setGridMode,
    gridSize,
    setGridSize,
  } = useAnalysis();

  const inputRef = useRef<HTMLInputElement>(null);
  const folderRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  useEffect(() => {
    const el = folderRef.current;
    if (!el) return;
    el.setAttribute("webkitdirectory", "");
    el.setAttribute("directory", "");
  }, []);

  const applyFiles = useCallback(
    (list: FileList | File[], append = false) => {
      const next = Array.from(list).filter(isAccepted);
      setFiles(append ? [...files, ...next] : next);
    },
    [files, setFiles]
  );

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

  const btn =
    "inline-flex items-center gap-1.5 rounded-lg border border-[var(--line)] px-3 py-2 text-xs font-medium text-slate-200 transition hover:border-[#7C3AED]/50 disabled:cursor-not-allowed disabled:opacity-40";
  const btnPrimary =
    "inline-flex items-center gap-1.5 rounded-lg bg-[#7C3AED] px-3 py-2 text-xs font-semibold text-white transition hover:bg-[#6D28D9] disabled:cursor-not-allowed disabled:opacity-40";

  return (
    <section className="panel space-y-3 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="panel-title">Workspace Controls</h2>
        <p className="text-[11px] text-[var(--wv-muted)]">
          {results.length} analyzed · {files.length} queued · jpg · jpeg · png · bmp
        </p>
      </div>

      <div className="flex flex-wrap items-stretch gap-3">
        <div
          className={cn(
            "flex min-w-[200px] flex-1 cursor-pointer items-center gap-3 rounded-lg border-2 border-dashed px-3 py-2.5 transition",
            dragging
              ? "border-[#7C3AED] bg-[#7C3AED]/10"
              : "border-[var(--line)] hover:border-[#7C3AED]/50",
            isAnalyzing && "pointer-events-none opacity-60"
          )}
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setDragging(false);
            if (event.dataTransfer.files?.length) {
              applyFiles(event.dataTransfer.files);
            }
          }}
          onClick={() => inputRef.current?.click()}
        >
          <UploadCloud className="h-5 w-5 shrink-0 text-[#A78BFA]" />
          <div className="min-w-0">
            <p className="text-xs font-medium text-white">Drag & Drop Upload</p>
            <p className="truncate text-[11px] text-[var(--wv-muted)]">
              {files.length > 0
                ? files.map((f) => f.webkitRelativePath || f.name).join(", ")
                : "Drop or click to browse"}
            </p>
          </div>
          <input
            ref={inputRef}
            type="file"
            accept=".jpg,.jpeg,.png,.bmp,image/jpeg,image/png,image/bmp"
            multiple
            className="hidden"
            onChange={(event) => {
              if (event.target.files) applyFiles(event.target.files);
            }}
          />
        </div>

        <button
          type="button"
          disabled={isAnalyzing}
          onClick={() => folderRef.current?.click()}
          className={btn}
        >
          <FolderOpen className="h-3.5 w-3.5" />
          Folder Upload
        </button>
        <input
          ref={folderRef}
          type="file"
          multiple
          className="hidden"
          onChange={(event) => {
            if (event.target.files) applyFiles(event.target.files);
          }}
        />

        <div className="hidden h-auto w-px self-stretch bg-[var(--line)] sm:block" />

        <label
          className={cn(
            "inline-flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-xs",
            gridMode === "automatic"
              ? "border-[#7C3AED] bg-[#7C3AED]/20 text-white"
              : "border-[var(--line)] text-slate-300"
          )}
        >
          <input
            type="radio"
            name="ribbon-grid-mode"
            checked={gridMode === "automatic"}
            disabled={isAnalyzing}
            onChange={() => setGridMode("automatic")}
          />
          Automatic Grid
        </label>
        <label
          className={cn(
            "inline-flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-xs",
            gridMode === "manual"
              ? "border-[#7C3AED] bg-[#7C3AED]/20 text-white"
              : "border-[var(--line)] text-slate-300"
          )}
        >
          <input
            type="radio"
            name="ribbon-grid-mode"
            checked={gridMode === "manual"}
            disabled={isAnalyzing}
            onChange={() => setGridMode("manual")}
          />
          Manual Grid
        </label>

        {gridMode === "manual" && (
          <div className="inline-flex items-center gap-2">
            <label
              htmlFor="ribbon-grid-size"
              className="text-[11px] uppercase tracking-wide text-[var(--wv-muted)]"
            >
              Grid Size
            </label>
            <input
              id="ribbon-grid-size"
              type="number"
              min={2}
              max={256}
              value={gridSize}
              disabled={isAnalyzing}
              onChange={(event) =>
                setGridSize(Math.min(256, Math.max(2, Number(event.target.value) || 2)))
              }
              className="w-20 rounded-lg border border-[var(--line)] bg-transparent px-2 py-1.5 text-xs text-white outline-none focus:border-[#7C3AED]"
              placeholder="52"
            />
          </div>
        )}

        <div className="hidden h-auto w-px self-stretch bg-[var(--line)] sm:block" />

        <button
          type="button"
          disabled={isAnalyzing || files.length === 0}
          onClick={analyze}
          className={btnPrimary}
        >
          <Play className="h-3.5 w-3.5" />
          {isAnalyzing ? "Analyzing…" : "Analyze Wafer"}
        </button>
        <button type="button" disabled={!results.length || isAnalyzing} onClick={exportCsv} className={btn}>
          <FileSpreadsheet className="h-3.5 w-3.5" />
          CSV
        </button>
        <button type="button" disabled={!results.length || isAnalyzing} onClick={exportJson} className={btn}>
          <FileJson className="h-3.5 w-3.5" />
          JSON
        </button>
        <button
          type="button"
          disabled
          title="PDF export planned for a later release"
          className={`${btn} opacity-40`}
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
    </section>
  );
}
