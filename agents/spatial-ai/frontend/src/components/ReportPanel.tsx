"use client";

import { useMemo } from "react";

import { useAnalysis } from "@/hooks/useAnalysis";
import {
  buildExportRows,
  computeBatchSummary,
  computeDefectDistribution,
  computeLotDistribution,
  computeLotSummary,
} from "@/utils/batchAggregates";
import { exportSessionCsv, exportSessionJson } from "@/utils/export";
import { formatPercent } from "@/utils/format";

export function ReportPanel() {
  const { results } = useAnalysis();
  const summary = useMemo(() => computeBatchSummary(results), [results]);
  const lots = useMemo(() => computeLotSummary(results), [results]);
  const defectDist = useMemo(() => computeDefectDistribution(results), [results]);
  const lotDist = useMemo(() => computeLotDistribution(results), [results]);

  if (!results.length) {
    return (
      <section className="panel p-5">
        <h2 className="panel-title mb-2">Batch Summary Report</h2>
        <p className="text-sm text-[var(--muted)]">
          Run a batch analysis to generate the enterprise report.
        </p>
      </section>
    );
  }

  return (
    <section className="panel space-y-6 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="panel-title">Batch Summary Report</h2>
          <p className="mt-1 text-xs text-[var(--muted)]">
            Built only from cached session API responses.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            className="rounded-lg border border-[var(--line)] px-3 py-2 text-xs font-medium"
            onClick={() => exportSessionCsv(buildExportRows(results))}
          >
            Export CSV
          </button>
          <button
            type="button"
            className="rounded-lg border border-[var(--line)] px-3 py-2 text-xs font-medium"
            onClick={() =>
              exportSessionJson({
                report: "batch_summary",
                generated_at: new Date().toISOString(),
                summary,
                lot_summary: lots,
                defect_distribution: defectDist,
                lot_distribution: lotDist,
                wafers: buildExportRows(results),
              })
            }
          >
            Export JSON
          </button>
          <button
            type="button"
            disabled
            title="PDF export planned for a later release"
            className="rounded-lg border border-[var(--line)] px-3 py-2 text-xs font-medium opacity-40"
          >
            Export PDF
          </button>
        </div>
      </div>

      <div>
        <h3 className="mb-2 text-sm font-semibold">Yield Statistics</h3>
        <dl className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4 text-sm">
          <Stat label="Total Wafers" value={String(summary.totalWafers)} />
          <Stat label="Average Yield" value={formatPercent(summary.averageYield)} />
          <Stat label="Highest Yield" value={formatPercent(summary.highestYield)} />
          <Stat label="Lowest Yield" value={formatPercent(summary.lowestYield)} />
          <Stat
            label="Average Confidence"
            value={formatPercent(summary.averageConfidence)}
          />
          <Stat label="Total Good Dies" value={String(summary.totalGoodDies)} />
          <Stat label="Total Fail Dies" value={String(summary.totalFailDies)} />
        </dl>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div>
          <h3 className="mb-2 text-sm font-semibold">LOT Distribution</h3>
          <ul className="space-y-1 text-sm">
            {lotDist.map((row) => (
              <li
                key={row.name}
                className="flex justify-between border-b border-[var(--line)] py-1"
              >
                <span className="font-mono text-xs">{row.name}</span>
                <span>{row.count}</span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="mb-2 text-sm font-semibold">Defect Distribution</h3>
          <ul className="space-y-1 text-sm">
            {defectDist.map((row) => (
              <li
                key={row.name}
                className="flex justify-between border-b border-[var(--line)] py-1"
              >
                <span>{row.name}</span>
                <span>{row.count}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div>
        <h3 className="mb-2 text-sm font-semibold">LOT Summary Detail</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--line)] text-left text-xs uppercase text-[var(--muted)]">
                <th className="py-2 pr-3">LOT</th>
                <th className="py-2 pr-3">Defect</th>
                <th className="py-2 pr-3">Wafers</th>
                <th className="py-2">Avg Yield</th>
              </tr>
            </thead>
            <tbody>
              {lots.map((lot) => (
                <tr key={lot.lot} className="border-b border-[var(--line)]">
                  <td className="py-2 pr-3 font-mono text-xs">{lot.lot}</td>
                  <td className="py-2 pr-3">{lot.defect}</td>
                  <td className="py-2 pr-3">{lot.waferCount}</td>
                  <td className="py-2 font-mono">{formatPercent(lot.averageYield)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-[var(--line)] px-3 py-2">
      <dt className="text-[11px] uppercase tracking-wide text-[var(--muted)]">{label}</dt>
      <dd className="mt-1 font-mono font-semibold">{value}</dd>
    </div>
  );
}
