"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { useAnalysis } from "@/wafervision/hooks/useAnalysis";
import {
  resolveFailDies,
  resolveGoodDies,
  resolveTotalDies,
  resolveYield,
} from "@/wafervision/utils/batchAggregates";
import { formatNumber, formatPercent } from "@/wafervision/utils/format";

const GOOD = "#1f9d63";
const FAIL = "#d64545";

export function YieldSummary() {
  const { selected } = useAnalysis();

  if (!selected?.yield_summary) {
    return (
      <section className="panel p-5">
        <h2 className="panel-title mb-3">Yield</h2>
        <p className="text-sm" style={{ color: "var(--muted)" }}>
          Awaiting backend yield_summary.
        </p>
      </section>
    );
  }

  const good = resolveGoodDies(selected);
  const fail = resolveFailDies(selected);
  const data = [
    { name: "Good", value: good, fill: GOOD },
    { name: "Fail", value: fail, fill: FAIL },
  ].filter((d) => d.value > 0);

  return (
    <section className="panel p-5">
      <h2 className="panel-title mb-3">Yield</h2>
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            innerRadius={48}
            outerRadius={70}
            paddingAngle={2}
          >
            {data.map((entry) => (
              <Cell key={entry.name} fill={entry.fill} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: "var(--panel)",
              border: "1px solid var(--line)",
              borderRadius: 8,
            }}
          />
        </PieChart>
      </ResponsiveContainer>
      <div className="mt-3 grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
        <Metric label="Yield %" value={formatPercent(resolveYield(selected))} />
        <Metric label="Good Dies" value={formatNumber(good)} />
        <Metric label="Fail Dies" value={formatNumber(fail)} />
        <Metric label="Total Dies" value={formatNumber(resolveTotalDies(selected))} />
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border p-2" style={{ borderColor: "var(--line)" }}>
      <div className="text-[11px] uppercase" style={{ color: "var(--muted)" }}>
        {label}
      </div>
      <div className="font-mono font-semibold">{value}</div>
    </div>
  );
}
