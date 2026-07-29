"use client";

import { useAnalysis } from "@/context/AnalysisContext";

export function GridConfiguration() {
  const { gridMode, setGridMode, gridSize, setGridSize, isAnalyzing, analyze, files } =
    useAnalysis();

  return (
    <section className="panel p-5">
      <h2 className="panel-title mb-4">Grid Configuration</h2>

      <div className="space-y-3">
        <label className="flex cursor-pointer items-center gap-3 rounded-lg border border-[var(--line)] px-3 py-3">
          <input
            type="radio"
            name="grid-mode"
            checked={gridMode === "automatic"}
            disabled={isAnalyzing}
            onChange={() => setGridMode("automatic")}
          />
          <div>
            <p className="text-sm font-medium">Automatic Grid Detection</p>
            <p className="text-xs text-[var(--muted)]">
              Default · backend estimates pitch & layout
            </p>
          </div>
        </label>

        <label className="flex cursor-pointer items-center gap-3 rounded-lg border border-[var(--line)] px-3 py-3">
          <input
            type="radio"
            name="grid-mode"
            checked={gridMode === "manual"}
            disabled={isAnalyzing}
            onChange={() => setGridMode("manual")}
          />
          <div>
            <p className="text-sm font-medium">Manual Grid</p>
            <p className="text-xs text-[var(--muted)]">Provide square grid size only</p>
          </div>
        </label>
      </div>

      {gridMode === "manual" && (
        <div className="mt-4">
          <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-[var(--muted)]">
            Grid Size
          </label>
          <input
            type="number"
            min={2}
            max={256}
            value={gridSize}
            disabled={isAnalyzing}
            onChange={(event) => setGridSize(Number(event.target.value) || 2)}
            className="w-full rounded-lg border border-[var(--line)] bg-transparent px-3 py-2 text-sm outline-none focus:border-signal-info"
            placeholder="52"
          />
          <p className="mt-1 text-xs text-[var(--muted)]">
            Sent as grid_size to POST /predict (rows = columns). Pitch / offset stay
            internal on the backend.
          </p>
        </div>
      )}

      <button
        type="button"
        disabled={isAnalyzing || files.length === 0}
        onClick={analyze}
        className="mt-5 w-full rounded-lg bg-ink-800 px-4 py-3 text-sm font-semibold text-white transition hover:bg-ink-700 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-ink-200 dark:text-ink-950 dark:hover:bg-white"
      >
        {isAnalyzing ? "Analyzing…" : "Analyze Wafer"}
      </button>
    </section>
  );
}
