"use client";

import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export function VizBarChart({
  series,
}: {
  series: { label: string; value: number }[];
}) {
  return (
    <ResponsiveContainer width="100%" height="90%">
      <BarChart data={series}>
        <XAxis dataKey="label" tick={{ fill: "#94A3B8", fontSize: 10 }} />
        <YAxis hide />
        <Tooltip
          contentStyle={{ background: "#111827", border: "1px solid #2D3748", borderRadius: 12 }}
        />
        <Bar dataKey="value" fill="#7C3AED" radius={[6, 6, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
