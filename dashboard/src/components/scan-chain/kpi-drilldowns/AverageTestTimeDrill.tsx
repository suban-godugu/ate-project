"use client";

import { memo, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { cn } from "@/lib/utils";
import type {
  TestTimeDistributionItem,
  TestTimeDistributionTab,
  TestTimeStatusData,
} from "@/lib/scan-chain/avgTestTimeDrillData";
import {
  TEST_TIME_DISTRIBUTION_BY_TAB,
  TEST_TIME_DISTRIBUTION_LABELS,
  TEST_TIME_DISTRIBUTION_TABS,
} from "@/lib/scan-chain/avgTestTimeDrillData";

const STATUS_COLORS = {
  optimal: "#22C55E",
  acceptable: "#EAB308",
  slow: "#EF4444",
};

export const TestTimeDistributionChart = memo(function TestTimeDistributionChart() {
  const [tab, setTab] = useState<TestTimeDistributionTab>("tester");

  const chartData = useMemo(() => {
    const items = [...(TEST_TIME_DISTRIBUTION_BY_TAB[tab] ?? [])];
    return items.sort((a, b) => b.avgSeconds - a.avgSeconds);
  }, [tab]);

  const xMax = useMemo(() => {
    const max = Math.max(...chartData.map((d) => d.avgSeconds), 18);
    return Math.ceil(max * 1.08 * 10) / 10;
  }, [chartData]);

  return (
    <div>
      <p className="mb-3 text-sm text-[#94A3B8]">Average test time across manufacturing dimensions</p>
      <div className="mb-3 flex flex-wrap gap-2">
        {TEST_TIME_DISTRIBUTION_TABS.map((item) => (
          <button
            key={item}
            type="button"
            onClick={() => setTab(item)}
            className={cn(
              "rounded-lg px-3 py-1.5 text-xs font-medium transition",
              tab === item
                ? "bg-[#8B5CF6] text-white"
                : "bg-[#1e293b]/60 text-[#94A3B8] hover:text-white"
            )}
          >
            {TEST_TIME_DISTRIBUTION_LABELS[item]}
          </button>
        ))}
      </div>
      <motion.div
        key={tab}
        initial={{ opacity: 0, x: 8 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.3 }}
        className="h-72 rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/60 p-4"
      >
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical" margin={{ top: 4, right: 64, left: 4, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" horizontal={false} />
            <XAxis
              type="number"
              domain={[0, xMax]}
              stroke="#64748B"
              fontSize={11}
              tickLine={false}
              tickFormatter={(v) => `${v} s`}
            />
            <YAxis type="category" dataKey="name" stroke="#64748B" fontSize={11} width={96} tickLine={false} />
            <Tooltip
              contentStyle={{
                background: "#111827",
                border: "1px solid #2D3748",
                borderRadius: "12px",
                fontSize: "12px",
              }}
              formatter={(value, _name, item) => {
                const row = item?.payload as TestTimeDistributionItem | undefined;
                return [`${Number(value ?? 0).toFixed(1)} s (${row?.sharePct.toFixed(1)}% share)`, "Avg Test Time"];
              }}
            />
            <Bar dataKey="avgSeconds" radius={[0, 6, 6, 0]} isAnimationActive>
              {chartData.map((_, index) => (
                <Cell key={`tt-dist-${index}`} fill={index === 0 ? "#7C3AED" : "#8B5CF6"} />
              ))}
              <LabelList
                dataKey="sharePct"
                position="right"
                formatter={(value) => `${Number(value).toFixed(1)}%`}
                className="fill-[#94A3B8] text-[10px]"
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </motion.div>
    </div>
  );
});

interface StatusProps {
  status: TestTimeStatusData;
}

export const TestTimeStatusChart = memo(function TestTimeStatusChart({ status }: StatusProps) {
  const pieData = useMemo(
    () => [
      { name: "Optimal", value: status.optimal, color: STATUS_COLORS.optimal },
      { name: "Acceptable", value: status.acceptable, color: STATUS_COLORS.acceptable },
      { name: "Slow", value: status.slow, color: STATUS_COLORS.slow },
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
          <p className="text-2xl font-bold text-white">{status.averageSeconds.toFixed(1)} s</p>
          <p className="text-xs text-slate-400">Average Test Time</p>
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
          Total Samples: {status.totalSamples.toLocaleString()}
        </p>
      </div>
    </motion.div>
  );
});
