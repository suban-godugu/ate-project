"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CostTrendPoint } from "@/types/dashboard";

interface CostTrendChartProps {
  data: CostTrendPoint[];
}

export function CostTrendChart({ data }: CostTrendChartProps) {
  return (
    <div id="cost" className="glass-card gradient-border p-6">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-white">Cost Trend Analysis</h3>
        <p className="text-sm text-slate-400">Daily total cost and cost per wafer — 7 days</p>
      </div>

      <div className="mb-2 flex justify-center">
        <div className="flex gap-6 text-xs text-slate-400">
          <span className="flex items-center gap-2">
            <span className="h-0.5 w-4 bg-[#7C3AED]" /> Total Cost ($K)
          </span>
          <span className="flex items-center gap-2">
            <span className="h-0.5 w-4 bg-[#06B6D4]" /> Cost per Wafer ($)
          </span>
        </div>
      </div>

      <div className="h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" />
            <XAxis
              dataKey="day"
              tick={{ fill: "#94A3B8", fontSize: 12 }}
              axisLine={{ stroke: "#2D3748" }}
            />
            <YAxis
              yAxisId="left"
              tick={{ fill: "#94A3B8", fontSize: 12 }}
              axisLine={{ stroke: "#2D3748" }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fill: "#94A3B8", fontSize: 12 }}
              axisLine={{ stroke: "#2D3748" }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#111827",
                border: "1px solid #2D3748",
                borderRadius: "12px",
                color: "#F1F5F9",
              }}
            />
            <Legend wrapperStyle={{ color: "#94A3B8", fontSize: 12 }} />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="totalCost"
              name="Total Cost ($K)"
              stroke="#7C3AED"
              strokeWidth={2.5}
              dot={{ fill: "#7C3AED", r: 4 }}
              activeDot={{ r: 6 }}
              animationDuration={1200}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="costPerWafer"
              name="Cost per Wafer ($)"
              stroke="#06B6D4"
              strokeWidth={2.5}
              dot={{ fill: "#06B6D4", r: 4 }}
              activeDot={{ r: 6 }}
              animationDuration={1200}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
