"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { useAnalysis } from "@/context/AnalysisContext";
import { formatPercent } from "@/utils/format";

export function YieldSummary() {
  const { selected } = useAnalysis();

  if (!selected?.yield_summary) {
    return (
      <section className="panel p-5">
        <h2 className="panel-title mb-2">Yield Panel</h2>
        <p className="text-sm text-[var(--muted)]">Awaiting backend yield_summary.</p>
      </section>
    );
  }

  const { good_dies, fail_dies, total_dies, yield_percent } = selected.yield_summary;
  const data = [
    { name: "Good", value: good_dies },
    { name: "Fail", value: fail_dies },
  ];

  return (
    <section className="panel p-5">
      <h2 className="panel-title mb-4">Yield Panel</h2>
      <div className="grid gap-4 md:grid-cols-[180px_1fr]">
        <div className="h-44">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                dataKey="value"
                nameKey="name"
                innerRadius={48}
                outerRadius={70}
                paddingAngle={2}
              >
                <Cell fill="#1f9d63" />
                <Cell fill="#d64545" />
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="grid grid-cols-2 gap-3 content-center">
          <Metric label="Yield %" value={formatPercent(yield_percent)} />
          <Metric label="Good Dies" value={String(good_dies)} />
          <Metric label="Fail Dies" value={String(fail_dies)} />
          <Metric label="Total Dies" value={String(total_dies)} />
        </div>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-[var(--line)] px-3 py-3">
      <p className="text-[11px] uppercase tracking-[0.14em] text-[var(--muted)]">{label}</p>
      <p className="mt-1 font-mono text-lg font-semibold">{value}</p>
    </div>
  );
}
