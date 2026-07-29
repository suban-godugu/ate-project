"use client";

import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import type { PatternScatterPoint } from "@/types/scanChain";

const clusterColors: Record<string, string> = {
  A: "#7C3AED",
  B: "#06B6D4",
  C: "#F97316",
  D: "#EAB308",
};

interface PatternScatterChartProps {
  data: PatternScatterPoint[];
  height?: number;
  yAxisName?: string;
}

export function PatternScatterChart({
  data,
  height = 260,
  yAxisName = "Similarity",
}: PatternScatterChartProps) {
  const grouped = Object.entries(
    data.reduce<Record<string, PatternScatterPoint[]>>((acc, point) => {
      acc[point.cluster] = acc[point.cluster] ?? [];
      acc[point.cluster].push(point);
      return acc;
    }, {})
  );

  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 8, right: 8, left: -8, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" />
          <XAxis
            type="number"
            dataKey="x"
            name="Coverage"
            domain={[0.4, 1]}
            stroke="#64748B"
            fontSize={11}
            tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
          />
          <YAxis
            type="number"
            dataKey="y"
            name={yAxisName}
            domain={[0.4, 1]}
            stroke="#64748B"
            fontSize={11}
            tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
          />
          <ZAxis range={[60, 200]} />
          <Tooltip
            cursor={{ strokeDasharray: "3 3" }}
            contentStyle={{
              background: "#111827",
              border: "1px solid #2D3748",
              borderRadius: "12px",
              fontSize: "12px",
            }}
            formatter={(_, __, props) => {
              const p = props.payload as PatternScatterPoint;
              return [`${p.patternId} · Cluster ${p.cluster}`, "Pattern"];
            }}
          />
          {grouped.map(([cluster, points]) => (
            <Scatter
              key={cluster}
              name={`Cluster ${cluster}`}
              data={points}
              fill={clusterColors[cluster] ?? "#7C3AED"}
            />
          ))}
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
