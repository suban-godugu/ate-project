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

import type { NamedCount } from "@/utils/batchAggregates";

export function ChartPanel({
  title,
  data,
  emptyMessage,
}: {
  title: string;
  data: NamedCount[];
  emptyMessage: string;
}) {
  const hasData = data.some((d) => d.count > 0);

  return (
    <section className="panel p-5">
      <h2 className="panel-title mb-4">{title}</h2>
      {!hasData ? (
        <p className="text-sm text-[var(--muted)]">{emptyMessage}</p>
      ) : (
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 24 }}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.35} />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 10 }}
                interval={0}
                angle={-25}
                textAnchor="end"
                height={50}
              />
              <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#1f4e79" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  );
}
