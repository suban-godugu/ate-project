"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { StackedCostPoint, TrendPoint } from "@/types/costIntelligence";

const tooltipStyle = {
  background: "#111827",
  border: "1px solid #2D3748",
  borderRadius: "12px",
  fontSize: "12px",
};

export function ModuleHorizontalBarChart({ data }: { data: TrendPoint[] }) {
  return (
    <div className="h-[260px]">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 0, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" horizontal={false} />
          <XAxis type="number" stroke="#64748B" fontSize={11} tickLine={false} unit="K" />
          <YAxis type="category" dataKey="label" stroke="#64748B" fontSize={11} width={90} tickLine={false} />
          <Tooltip contentStyle={tooltipStyle} formatter={(v) => [`$${v}K`, "Cost"]} />
          <Bar dataKey="value" fill="#7C3AED" radius={[0, 6, 6, 0]} isAnimationActive />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

const stackColors = {
  equipment: "#7C3AED",
  tester: "#06B6D4",
  engineering: "#F97316",
  pattern: "#EAB308",
  repair: "#EF4444",
  retest: "#64748B",
};

export function StackedCostBarChart({ data }: { data: StackedCostPoint[] }) {
  return (
    <div className="h-[280px]">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" vertical={false} />
          <XAxis dataKey="label" stroke="#64748B" fontSize={11} tickLine={false} />
          <YAxis stroke="#64748B" fontSize={11} tickLine={false} unit="K" />
          <Tooltip contentStyle={tooltipStyle} />
          <Legend wrapperStyle={{ fontSize: "11px", color: "#94A3B8" }} />
          <Bar dataKey="equipment" stackId="a" fill={stackColors.equipment} name="Equipment" isAnimationActive />
          <Bar dataKey="tester" stackId="a" fill={stackColors.tester} name="Tester" isAnimationActive />
          <Bar dataKey="engineering" stackId="a" fill={stackColors.engineering} name="Engineering" isAnimationActive />
          <Bar dataKey="pattern" stackId="a" fill={stackColors.pattern} name="Pattern Execution" isAnimationActive />
          <Bar dataKey="repair" stackId="a" fill={stackColors.repair} name="Repair" isAnimationActive />
          <Bar dataKey="retest" stackId="a" fill={stackColors.retest} name="Retest" isAnimationActive />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
