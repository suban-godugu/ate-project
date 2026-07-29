"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TrendPoint } from "@/types/scanChain";

interface TrendLineChartProps {
  data: TrendPoint[];
  lines?: { key: keyof TrendPoint; color: string; name: string }[];
  height?: number;
}

export function TrendLineChart({
  data,
  lines = [{ key: "value", color: "#7C3AED", name: "Value" }],
  height = 240,
}: TrendLineChartProps) {
  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" vertical={false} />
          <XAxis dataKey="label" stroke="#64748B" fontSize={11} tickLine={false} />
          <YAxis stroke="#64748B" fontSize={11} tickLine={false} />
          <Tooltip
            contentStyle={{
              background: "#111827",
              border: "1px solid #2D3748",
              borderRadius: "12px",
              fontSize: "12px",
            }}
          />
          {lines.length > 1 && <Legend wrapperStyle={{ fontSize: "12px" }} />}
          {lines.map((line) => (
            <Line
              key={String(line.key)}
              type="monotone"
              dataKey={line.key}
              stroke={line.color}
              strokeWidth={2}
              dot={false}
              name={line.name}
              isAnimationActive
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

interface TrendAreaChartProps {
  data: TrendPoint[];
  height?: number;
}

export function TrendAreaChart({ data, height = 240 }: TrendAreaChartProps) {
  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <defs>
            <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#7C3AED" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#7C3AED" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" vertical={false} />
          <XAxis dataKey="label" stroke="#64748B" fontSize={11} tickLine={false} />
          <YAxis stroke="#64748B" fontSize={11} tickLine={false} />
          <Tooltip
            contentStyle={{
              background: "#111827",
              border: "1px solid #2D3748",
              borderRadius: "12px",
              fontSize: "12px",
            }}
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke="#7C3AED"
            strokeWidth={2}
            fill="url(#areaGradient)"
            isAnimationActive
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
