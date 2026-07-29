"use client";

import { useAnalysis } from "@/hooks/useAnalysis";
import {
  displayLot,
  formatPercent,
  readDefectType,
  readWaferName,
  toDataUrl,
} from "@/utils/format";

function Thumb({ label, base64 }: { label: string; base64?: string }) {
  const src = toDataUrl(base64);
  return (
    <div className="min-w-[120px]">
      <p className="mb-1 text-[10px] uppercase tracking-wide text-[var(--muted)]">
        {label}
      </p>
      <div className="flex aspect-square items-center justify-center rounded border border-[var(--line)] bg-ink-950/5 p-1 dark:bg-black/20">
        {src ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={src} alt={label} className="max-h-full max-w-full object-contain" />
        ) : (
          <span className="text-[10px] text-[var(--muted)]">N/A</span>
        )}
      </div>
    </div>
  );
}

export function WaferComparison() {
  const { results, comparisonIndices, clearComparison, toggleComparison } =
    useAnalysis();

  const selected = comparisonIndices
    .map((index) => ({ index, wafer: results[index] }))
    .filter((row) => row.wafer);

  return (
    <section className="panel p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="panel-title">Comparison View</h2>
          <p className="mt-1 text-xs text-[var(--muted)]">
            Select 2+ wafers from the sidebar checkboxes. No extra API calls.
          </p>
        </div>
        <button
          type="button"
          disabled={!comparisonIndices.length}
          onClick={clearComparison}
          className="rounded-lg border border-[var(--line)] px-3 py-1.5 text-xs disabled:opacity-40"
        >
          Clear Selection ({comparisonIndices.length})
        </button>
      </div>

      {selected.length < 2 ? (
        <p className="text-sm text-[var(--muted)]">
          Choose at least two wafers to compare side-by-side.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-[var(--line)] text-left text-xs uppercase tracking-wide text-[var(--muted)]">
                <th className="px-2 py-2">Wafer</th>
                <th className="px-2 py-2">Original</th>
                <th className="px-2 py-2">Overlay</th>
                <th className="px-2 py-2">Density</th>
                <th className="px-2 py-2">GradCAM</th>
                <th className="px-2 py-2">Yield</th>
                <th className="px-2 py-2">Defect</th>
                <th className="px-2 py-2">LOT</th>
                <th className="px-2 py-2">Confidence</th>
                <th className="px-2 py-2" />
              </tr>
            </thead>
            <tbody>
              {selected.map(({ index, wafer }) => (
                <tr key={`${wafer.wafer_id}-${index}`} className="border-b border-[var(--line)] align-top">
                  <td className="px-2 py-3 font-mono text-xs">
                    {readWaferName(wafer)}
                  </td>
                  <td className="px-2 py-3">
                    <Thumb label="Original" base64={wafer.images?.original} />
                  </td>
                  <td className="px-2 py-3">
                    <Thumb label="Overlay" base64={wafer.images?.overlay} />
                  </td>
                  <td className="px-2 py-3">
                    <Thumb label="Density" base64={wafer.images?.density} />
                  </td>
                  <td className="px-2 py-3">
                    <Thumb label="GradCAM" base64={wafer.images?.gradcam} />
                  </td>
                  <td className="px-2 py-3 font-mono">
                    {formatPercent(wafer.yield_summary?.yield_percent)}
                  </td>
                  <td className="px-2 py-3">{readDefectType(wafer)}</td>
                  <td className="px-2 py-3 font-mono">{displayLot(wafer)}</td>
                  <td className="px-2 py-3 font-mono">
                    {formatPercent(wafer.classification?.confidence)}
                  </td>
                  <td className="px-2 py-3">
                    <button
                      type="button"
                      className="text-xs text-signal-fail underline"
                      onClick={() => toggleComparison(index)}
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
