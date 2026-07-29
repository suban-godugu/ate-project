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
import type { ReactNode } from "react";

export interface ChartDatum {
  name: string;
  count: number;
}

interface ChartPanelProps {
  title: string;
  data: ChartDatum[];
  emptyMessage?: string;
  footer?: ReactNode;
}

export function ChartPanel({ title, data, emptyMessage = "No data", footer }: ChartPanelProps) {
  const hasData = data.some((d) => d.count > 0);

  return (
    <div className="panel p-4">
      <h3 className="panel-title mb-3">{title}</h3>
      {!hasData ? (
        <p className="py-8 text-center text-sm text-[var(--muted)]">{emptyMessage}</p>
      ) : (
        <ResponsiveContainer width="100%" height={224}>
          <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 48 }}>
            <CartesianGrid strokeDasharray="4 4" stroke="var(--line)" />
            <XAxis
              dataKey="name"
              tick={{ fill: "var(--muted)", fontSize: 10 }}
              angle={-25}
              textAnchor="end"
              interval={0}
              height={56}
            />
            <YAxis tick={{ fill: "var(--muted)", fontSize: 11 }} allowDecimals={false} />
            <Tooltip
              contentStyle={{
                background: "var(--panel)",
                border: "1px solid var(--line)",
                borderRadius: 8,
                color: "var(--text)",
              }}
            />
            <Bar dataKey="count" fill="#7c3aed" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      )}
      {footer}
    </div>
  );
}
