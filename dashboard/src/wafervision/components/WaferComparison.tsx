"use client";

import { useAnalysis } from "@/wafervision/hooks/useAnalysis";
import {
  resolveConfidence,
  resolveDefect,
  resolveLot,
  resolveYield,
} from "@/wafervision/utils/batchAggregates";
import { displayWaferName, formatPercent } from "@/wafervision/utils/format";

export function WaferComparison() {
  const { results, comparisonIndices, clearComparison } = useAnalysis();
  const rows = comparisonIndices
    .map((i) => ({ index: i, result: results[i] }))
    .filter((r) => r.result);

  return (
    <section className="panel p-5 space-y-3">
      <div className="flex items-center justify-between gap-3">
        <h2 className="panel-title">Comparison View</h2>
        <button
          type="button"
          onClick={clearComparison}
          className="rounded-lg border px-3 py-1 text-xs"
          style={{ borderColor: "var(--line)" }}
        >
          Clear comparison
        </button>
      </div>
      {!rows.length ? (
        <p className="text-sm" style={{ color: "var(--muted)" }}>
          Select wafers with comparison checkboxes in Wafer Results.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-[11px] uppercase" style={{ color: "var(--muted)" }}>
                {["Wafer", "Defect", "LOT", "Yield", "Confidence"].map((h) => (
                  <th key={h} className="px-2 py-2 text-left">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map(({ index, result }) => (
                <tr key={index} className="border-t" style={{ borderColor: "var(--line)" }}>
                  <td className="px-2 py-2">{displayWaferName(result)}</td>
                  <td className="px-2 py-2">{resolveDefect(result)}</td>
                  <td className="px-2 py-2 font-mono">{resolveLot(result)}</td>
                  <td className="px-2 py-2 font-mono">{formatPercent(resolveYield(result))}</td>
                  <td className="px-2 py-2 font-mono">{formatPercent(resolveConfidence(result))}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
