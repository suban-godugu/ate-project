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
import type { LotFailData } from "@/types/scanChain";

export function FailureByLotChart({ data }: { data: LotFailData[] }) {
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
            dataKey="lot"
            stroke="#64748B"
            fontSize={10}
            width={90}
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
          <Bar dataKey="failCount" fill="#EF4444" radius={[0, 6, 6, 0]} isAnimationActive />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
