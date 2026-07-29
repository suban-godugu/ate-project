"use client";

import { memo, useMemo } from "react";
import { motion } from "framer-motion";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { CoverageStatusSlice } from "@/types/scanCoverage";

const COLORS = {
  full: "#22C55E",
  partial: "#EAB308",
  uncovered: "#EF4444",
};

interface Props {
  status: CoverageStatusSlice;
}

export const CoverageStatus = memo(function CoverageStatus({ status }: Props) {
  const pieData = useMemo(
    () => [
      {
        name: "Fully Covered",
        value: status.fullyCovered,
        count: Math.round((status.fullyCovered / 100) * status.entityCount),
        color: COLORS.full,
      },
      {
        name: "Partially Covered",
        value: status.partiallyCovered,
        count: Math.round((status.partiallyCovered / 100) * status.entityCount),
        color: COLORS.partial,
      },
      {
        name: "Uncovered",
        value: status.uncovered,
        count: Math.round((status.uncovered / 100) * status.entityCount),
        color: COLORS.uncovered,
      },
    ],
    [status]
  );

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.35 }}
      className="grid gap-4 rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/60 p-4 lg:grid-cols-[1.2fr_1fr]"
    >
      <div className="relative h-[280px] w-full min-w-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              innerRadius={72}
              outerRadius={104}
              paddingAngle={3}
              dataKey="value"
              stroke="none"
              isAnimationActive
            >
              {pieData.map((entry) => (
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
              formatter={(value, name) => {
                const num = Number(value ?? 0);
                return [`${num.toFixed(1)}%`, name];
              }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <p className="text-2xl font-bold text-white">{status.fullyCovered.toFixed(1)}%</p>
          <p className="text-xs text-slate-400">Fully Covered</p>
        </div>
      </div>
      <div className="flex flex-col justify-center gap-3">
        {pieData.map((item) => (
          <div
            key={item.name}
            className="flex items-center justify-between rounded-lg border border-[#2D3748]/80 bg-[#0B0F1A]/50 px-3 py-2.5"
          >
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: item.color }} />
              <span className="text-sm text-[#CBD5E1]">{item.name}</span>
            </div>
            <div className="text-right">
              <p className="text-sm font-semibold tabular-nums text-white">{item.value.toFixed(1)}%</p>
              <p className="text-[11px] text-[#94A3B8]">{item.count.toLocaleString()} entities</p>
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
});
