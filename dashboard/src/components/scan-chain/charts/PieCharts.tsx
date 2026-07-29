"use client";

import {
  Cell,
  Pie,
  PieChart as RechartsPie,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { HealthSegment } from "@/types/scanChain";

interface DonutChartProps {
  data: HealthSegment[];
  centerLabel?: string;
  centerValue?: string | number;
}

export function DonutChart({ data, centerLabel, centerValue }: DonutChartProps) {
  const total = data.reduce((sum, d) => sum + d.value, 0);

  return (
    <div className="relative h-[260px]">
      <ResponsiveContainer width="100%" height="100%">
        <RechartsPie>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={70}
            outerRadius={100}
            paddingAngle={3}
            dataKey="value"
            stroke="none"
            isAnimationActive
          >
            {data.map((entry) => (
              <Cell key={entry.name} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: "#111827",
              border: "1px solid #2D3748",
              borderRadius: "12px",
              fontSize: "12px",
            }}
            formatter={(value, name) => [
              `${value} (${(((value as number) / total) * 100).toFixed(1)}%)`,
              name,
            ]}
          />
        </RechartsPie>
      </ResponsiveContainer>
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
        <p className="text-2xl font-bold text-white">
          {centerValue ?? total.toLocaleString()}
        </p>
        {centerLabel && (
          <p className="text-xs text-slate-400">{centerLabel}</p>
        )}
      </div>
    </div>
  );
}

interface DistributionPieProps {
  data: { name: string; value: number; color: string }[];
}

export function DistributionPie({ data }: DistributionPieProps) {
  return (
    <div className="h-[240px]">
      <ResponsiveContainer width="100%" height="100%">
        <RechartsPie>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            outerRadius={90}
            dataKey="value"
            stroke="none"
            label={({ name, percent }) =>
              `${name} ${((percent ?? 0) * 100).toFixed(0)}%`
            }
            labelLine={{ stroke: "#64748B" }}
            isAnimationActive
          >
            {data.map((entry) => (
              <Cell key={entry.name} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: "#111827",
              border: "1px solid #2D3748",
              borderRadius: "12px",
              fontSize: "12px",
            }}
          />
        </RechartsPie>
      </ResponsiveContainer>
    </div>
  );
}
