"use client";

import { memo, useMemo } from "react";
import { motion } from "framer-motion";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { DiagnosisConfidenceStatusData } from "@/lib/scan-chain/avgDiagnosisConfidenceDrillData";

const STATUS_COLORS = {
  high: "#22C55E",
  medium: "#EAB308",
  low: "#EF4444",
};

interface Props {
  status: DiagnosisConfidenceStatusData;
}

export const DiagnosisConfidenceStatusChart = memo(function DiagnosisConfidenceStatusChart({
  status,
}: Props) {
  const pieData = useMemo(
    () => [
      { name: "High Confidence", value: status.high, color: STATUS_COLORS.high },
      { name: "Medium Confidence", value: status.medium, color: STATUS_COLORS.medium },
      { name: "Low Confidence", value: status.low, color: STATUS_COLORS.low },
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
              formatter={(value, name) => [`${Number(value ?? 0).toFixed(1)}%`, name]}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <p className="text-2xl font-bold text-white">{status.average}%</p>
          <p className="text-xs text-slate-400">Average Confidence</p>
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
            <p className="text-sm font-semibold tabular-nums text-white">{item.value.toFixed(1)}%</p>
          </div>
        ))}
        <p className="mt-1 text-center text-[11px] text-[#64748B]">
          Total Diagnosis Confidence: {status.average}%
        </p>
      </div>
    </motion.div>
  );
});
