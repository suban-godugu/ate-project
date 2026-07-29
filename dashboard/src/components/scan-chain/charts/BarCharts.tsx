"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ChipFailData, TrendPoint } from "@/types/scanChain";

interface HorizontalBarChartProps {
  data: ChipFailData[];
}

export function HorizontalBarChart({ data }: HorizontalBarChartProps) {
  return (
    <div className="h-[280px]">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 0, right: 16, left: 0, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" horizontal={false} />
          <XAxis type="number" stroke="#64748B" fontSize={11} tickLine={false} />
          <YAxis
            type="category"
            dataKey="chip"
            stroke="#64748B"
            fontSize={10}
            width={110}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              background: "#111827",
              border: "1px solid #2D3748",
              borderRadius: "12px",
              fontSize: "12px",
            }}
          />
          <Bar
            dataKey="failCount"
            fill="#7C3AED"
            radius={[0, 6, 6, 0]}
            isAnimationActive
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

interface VerticalBarChartProps {
  data: TrendPoint[];
  dataKey?: string;
  color?: string;
}

export function VerticalBarChart({
  data,
  dataKey = "value",
  color = "#7C3AED",
}: VerticalBarChartProps) {
  return (
    <div className="h-[240px]">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
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
          <Bar
            dataKey={dataKey}
            fill={color}
            radius={[6, 6, 0, 0]}
            isAnimationActive
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
