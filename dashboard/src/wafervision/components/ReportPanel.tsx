"use client";

import { useMemo } from "react";
import { useAnalysis } from "@/wafervision/hooks/useAnalysis";
import {
  batchSummary,
  defectDistribution,
  exportRows,
  lotDistribution,
  lotSummary,
} from "@/wafervision/utils/batchAggregates";
import { downloadCsv, downloadJson, timestampStamp } from "@/wafervision/utils/export";
import { formatPercent } from "@/wafervision/utils/format";

export function ReportPanel() {
  const { results, isAnalyzing } = useAnalysis();
  const summary = useMemo(() => batchSummary(results), [results]);
  const lots = useMemo(() => lotSummary(results), [results]);
  const defects = useMemo(() => defectDistribution(results), [results]);
  const lotDist = useMemo(() => lotDistribution(results), [results]);

  if (!results.length) {
    return (
      <section className="panel p-5">
        <h2 className="panel-title mb-2">Reports</h2>
        <p className="text-sm" style={{ color: "var(--muted)" }}>
          Run a batch analysis to generate the enterprise report.
        </p>
      </section>
    );
  }

  const stamp = timestampStamp();
  const disabled = isAnalyzing;

  const onCsv = () => {
    const rows = exportRows(results);
    downloadCsv(
      `wafervision-batch-${stamp}.csv`,
      ["Wafer Name", "Defect", "LOT", "Yield", "Confidence", "Good Dies", "Fail Dies", "Total Dies"],
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

  const onJson = () => {
    downloadJson(`wafervision-batch-${stamp}.json`, {
      report: "batch_summary",
      generated_at: new Date().toISOString(),
      summary,
      lot_summary: lots,
      defect_distribution: defects,
      lot_distribution: lotDist,
      wafers: exportRows(results),
    });
  };

  const stats = [
    { label: "Total Wafers", value: summary.totalWafers },
    { label: "Average Yield", value: formatPercent(summary.averageYield) },
    { label: "Highest Yield", value: formatPercent(summary.highestYield) },
    { label: "Lowest Yield", value: formatPercent(summary.lowestYield) },
    { label: "Average Confidence", value: formatPercent(summary.averageConfidence) },
    { label: "Total Good Dies", value: summary.totalGoodDies },
    { label: "Total Fail Dies", value: summary.totalFailDies },
  ];

  return (
    <div className="space-y-4">
      <section className="panel p-5 flex flex-wrap items-center justify-between gap-3">
        <h2 className="panel-title">Enterprise Report</h2>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={disabled}
            onClick={onCsv}
            className="rounded-lg border px-3 py-1.5 text-xs disabled:opacity-40"
            style={{ borderColor: "var(--line)" }}
          >
            Export CSV
          </button>
          <button
            type="button"
            disabled={disabled}
            onClick={onJson}
            className="rounded-lg border px-3 py-1.5 text-xs disabled:opacity-40"
            style={{ borderColor: "var(--line)" }}
          >
            Export JSON
          </button>
          <button
            type="button"
            disabled
            title="PDF export planned for a later release."
            className="rounded-lg border px-3 py-1.5 text-xs opacity-40 cursor-not-allowed"
            style={{ borderColor: "var(--line)" }}
          >
            Export PDF
          </button>
        </div>
      </section>

      <section className="panel p-5">
        <h2 className="panel-title mb-3">Yield Statistics</h2>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-4">
          {stats.map((s) => (
            <div key={s.label} className="rounded-lg border p-3" style={{ borderColor: "var(--line)" }}>
              <div className="text-[11px] uppercase" style={{ color: "var(--muted)" }}>
                {s.label}
              </div>
              <div className="mt-1 font-mono text-lg font-semibold">{s.value}</div>
            </div>
          ))}
        </div>
      </section>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <section className="panel p-5">
          <h2 className="panel-title mb-3">LOT Distribution</h2>
          <ul className="space-y-1 text-sm">
            {lotDist.map((d) => (
              <li key={d.name} className="flex justify-between border-b py-1" style={{ borderColor: "var(--line)" }}>
                <span>{d.name}</span>
                <span className="font-mono">{d.count}</span>
              </li>
            ))}
          </ul>
        </section>
        <section className="panel p-5">
          <h2 className="panel-title mb-3">Defect Distribution</h2>
          <ul className="space-y-1 text-sm">
            {defects.map((d) => (
              <li key={d.name} className="flex justify-between border-b py-1" style={{ borderColor: "var(--line)" }}>
                <span>{d.name}</span>
                <span className="font-mono">{d.count}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>

      <section className="panel p-5">
        <h2 className="panel-title mb-3">LOT Summary Detail</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-[11px] uppercase" style={{ color: "var(--muted)" }}>
                {["LOT", "Defect", "Wafers", "Avg Yield"].map((h) => (
                  <th key={h} className="px-2 py-2 text-left">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {lots.map((l) => (
                <tr key={l.lot} className="border-t" style={{ borderColor: "var(--line)" }}>
                  <td className="px-2 py-2 font-mono">{l.lot}</td>
                  <td className="px-2 py-2">{l.defect}</td>
                  <td className="px-2 py-2 font-mono">{l.count}</td>
                  <td className="px-2 py-2 font-mono">{formatPercent(l.avgYield)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
