import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  PolarAngleAxis,
  RadialBar,
  RadialBarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { riskHex } from "@/lib/format";
import type { RiskLevel } from "@/lib/types";

const TOOLTIP = {
  contentStyle: {
    background: "#10131d",
    border: "1px solid rgba(255,255,255,0.10)",
    borderRadius: 8,
    fontSize: 12,
  },
  labelStyle: { color: "#c2c9dc" },
  itemStyle: { color: "#e9edf7" },
};

export function RiskDonut({ data }: { data: Record<string, number> }) {
  const rows = Object.entries(data)
    .filter(([, value]) => value > 0)
    .map(([name, value]) => ({ name, value }));

  if (rows.length === 0) {
    return <p className="py-10 text-center text-xs text-ink-400">No risk data yet</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie data={rows} dataKey="value" nameKey="name" innerRadius={55} outerRadius={85} strokeWidth={0}>
          {rows.map((row) => (
            <Cell key={row.name} fill={riskHex[row.name as RiskLevel] ?? "#818cf8"} />
          ))}
        </Pie>
        <Tooltip {...TOOLTIP} />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function RiskScoreGauge({ score, level }: { score: number; level: RiskLevel }) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <RadialBarChart
        data={[{ name: "risk", value: score }]}
        innerRadius="70%"
        outerRadius="100%"
        startAngle={210}
        endAngle={-30}
      >
        <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
        <RadialBar dataKey="value" cornerRadius={8} fill={riskHex[level]} background={{ fill: "rgba(255,255,255,0.06)" }} />
      </RadialBarChart>
    </ResponsiveContainer>
  );
}

export function ConfidenceBars({
  data,
}: {
  data: Array<{ name: string; value: number }>;
}) {
  if (data.length === 0) {
    return <p className="py-10 text-center text-xs text-ink-400">No blocks to compare</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={Math.max(180, data.length * 42)}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 24, top: 4, bottom: 4 }}>
        <XAxis
          type="number"
          domain={[0, 100]}
          tick={{ fill: "#646d84", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          unit="%"
        />
        <YAxis
          type="category"
          dataKey="name"
          width={140}
          tick={{ fill: "#8e97ae", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip {...TOOLTIP} formatter={(value) => [`${value}%`, "Confidence"]} />
        <Bar dataKey="value" fill="#6366f1" radius={[0, 6, 6, 0]} barSize={16} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function CategoryCountBars({
  data,
}: {
  data: Array<{ name: string; value: number }>;
}) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ left: 0, right: 8, top: 8, bottom: 4 }}>
        <XAxis
          dataKey="name"
          tick={{ fill: "#8e97ae", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          interval={0}
        />
        <YAxis
          allowDecimals={false}
          tick={{ fill: "#646d84", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip {...TOOLTIP} formatter={(value) => [`${value}`, "Actions"]} />
        <Bar dataKey="value" fill="#818cf8" radius={[6, 6, 0, 0]} barSize={34} />
      </BarChart>
    </ResponsiveContainer>
  );
}
