"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getIngestionStats } from "@/lib/api";

export function StatsPanel() {
  const { data } = useQuery({
    queryKey: ["ingestion-stats"],
    queryFn: getIngestionStats,
    refetchInterval: 5000,
  });

  const cards = [
    { label: "Total Uploads", value: data?.total_uploads ?? 0 },
    { label: "Completed", value: data?.completed ?? 0 },
    { label: "Failed", value: data?.failed ?? 0 },
    { label: "Processing", value: data?.processing ?? 0 },
    { label: "Records Accepted", value: data?.total_records_accepted ?? 0 },
  ];

  const chart = (data?.by_parser || []).map((p: { parser_id: string; upload_count: number; records_accepted: number }) => ({
    name: p.parser_id,
    uploads: p.upload_count,
    records: p.records_accepted,
  }));

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        {cards.map((c) => (
          <div key={c.label} className="glass-panel rounded-2xl p-4">
            <div className="text-xs uppercase tracking-wide text-[var(--muted)]">{c.label}</div>
            <div className="mt-2 text-2xl font-semibold">{c.value}</div>
          </div>
        ))}
      </div>
      <div className="glass-panel rounded-2xl p-4">
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
          Parser Statistics
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chart}>
              <CartesianGrid stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />
              <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
              <YAxis stroke="#94a3b8" fontSize={11} />
              <Tooltip
                contentStyle={{
                  background: "#111827",
                  border: "1px solid rgba(255,255,255,0.1)",
                }}
              />
              <Bar dataKey="uploads" fill="#7C3AED" radius={[6, 6, 0, 0]} />
              <Bar dataKey="records" fill="#38bdf8" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
