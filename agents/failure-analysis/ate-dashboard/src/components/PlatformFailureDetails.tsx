"use client";

import { memo, useMemo } from "react";
import type { PlatformFailureLatest } from "@/lib/platformFailureCharts";

type Props = {
  latest: PlatformFailureLatest | null | undefined;
};

export const PlatformFailureDetails = memo(function PlatformFailureDetails({ latest }: Props) {
  const report = latest?.report;
  const meta = latest?.metadata || {};
  const metrics = latest?.metrics;

  const wafers = useMemo(
    () => Object.entries(report?.wafer_statistics || report?.yield?.wafer_stats || {}),
    [report],
  );
  const testers = useMemo(() => Object.entries(report?.tester_analysis || {}), [report]);
  const patterns = useMemo(() => Object.entries(report?.pattern_analysis || {}).slice(0, 12), [report]);
  const chains = useMemo(() => Object.entries(report?.chain_analysis || {}).slice(0, 12), [report]);

  if (!latest || latest.status !== "completed") return null;

  return (
    <section className="space-y-3">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
        Platform Failure Details
      </h2>
      <div className="glass-panel rounded-2xl p-4">
        <div className="mb-4 flex flex-wrap gap-2 text-xs">
          <Chip label="Job" value={String(latest.job_id || latest.upload_id || "—")} />
          <Chip label="File" value={String(meta.file_name || "—")} />
          <Chip label="Module" value={String(meta.module || "—")} />
          <Chip label="Records" value={String(metrics?.total_tests ?? "—")} />
          <Chip label="PASS" value={String(metrics?.total_passed ?? 0)} />
          <Chip label="FAIL" value={String(metrics?.total_failed ?? 0)} />
          <Chip
            label="OTHER"
            value={String(
              (metrics as { other_count?: number } | undefined)?.other_count ??
                Math.max(
                  Number(metrics?.total_tests || 0) -
                    Number(metrics?.total_passed || 0) -
                    Number(metrics?.total_failed || 0),
                  0,
                ),
            )}
          />
          <Chip label="Yield" value={`${Number(metrics?.yield_pct ?? report?.yield?.yield_pct ?? 0).toFixed(1)}%`} />
          <Chip label="Fail rate" value={`${Number(metrics?.overall_failure_rate ?? 0).toFixed(2)}%`} />
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <DetailTable
            title="Wafer statistics"
            headers={["Wafer", "Total", "Pass", "Fail", "Other"]}
            rows={wafers.map(([id, s]) => [
              id,
              String(s.total ?? 0),
              String(s.pass ?? 0),
              String(s.fail ?? 0),
              String(s.other ?? Math.max(Number(s.total || 0) - Number(s.pass || 0) - Number(s.fail || 0), 0)),
            ])}
            empty="No wafer statistics in this report"
          />
          <DetailTable
            title="Tester breakdown"
            headers={["Tester", "Records"]}
            rows={testers.map(([id, count]) => [id, String(count)])}
            empty="No tester breakdown in this report"
          />
          <DetailTable
            title="Top patterns"
            headers={["Pattern", "Hits"]}
            rows={patterns.map(([id, count]) => [id, String(count)])}
            empty="No pattern names in dataset"
          />
          <DetailTable
            title="Top scan chains"
            headers={["Chain", "Hits"]}
            rows={chains.map(([id, count]) => [id, String(count)])}
            empty="No scan-chain names in dataset"
          />
        </div>
      </div>
    </section>
  );
});

function Chip({ label, value }: { label: string; value: string }) {
  return (
    <span className="rounded-full border border-[var(--border)] bg-white/5 px-2.5 py-1 text-[var(--muted)]">
      <strong className="mr-1 text-white">{label}:</strong>
      {value}
    </span>
  );
}

function DetailTable({
  title,
  headers,
  rows,
  empty,
}: {
  title: string;
  headers: string[];
  rows: string[][];
  empty: string;
}) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[#0A1020]/50 p-3">
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--accent)]">
        {title}
      </h3>
      {rows.length ? (
        <div className="max-h-56 overflow-auto">
          <table className="w-full border-collapse text-left text-xs">
            <thead>
              <tr>
                {headers.map((h) => (
                  <th key={h} className="sticky top-0 bg-[#0A1020] px-1.5 py-1 text-[10px] uppercase text-[var(--muted)]">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr key={`${row[0]}-${i}`} className="border-t border-[var(--border)]/70">
                  {row.map((cell, j) => (
                    <td
                      key={`${i}-${j}`}
                      className={`px-1.5 py-1 text-slate-200 ${j === 0 ? "max-w-[180px] truncate" : "text-right tabular-nums text-[var(--accent)]"}`}
                      title={cell}
                    >
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="py-6 text-center text-xs text-[var(--muted)]">{empty}</p>
      )}
    </div>
  );
}
