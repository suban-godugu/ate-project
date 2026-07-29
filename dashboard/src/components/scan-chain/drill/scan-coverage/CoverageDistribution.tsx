"use client";

import { memo, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { cn } from "@/lib/utils";
import type { CoverageDistributionItem, CoverageDistributionTab } from "@/types/scanCoverage";

const TABS: CoverageDistributionTab[] = ["Module", "Product", "Pattern", "Vector", "Tester", "Wafer"];

interface Props {
  distributionByTab: Record<CoverageDistributionTab, CoverageDistributionItem[]>;
}

export const CoverageDistribution = memo(function CoverageDistribution({ distributionByTab }: Props) {
  const [tab, setTab] = useState<CoverageDistributionTab>("Module");

  const chartData = useMemo(() => {
    const items = [...(distributionByTab[tab] ?? [])];
    return items.sort((a, b) => b.coveragePct - a.coveragePct);
  }, [distributionByTab, tab]);

  return (
    <div>
      <p className="mb-3 text-sm text-[#94A3B8]">Coverage distribution across manufacturing dimensions</p>
      <div className="mb-3 flex flex-wrap gap-2">
        {TABS.map((item) => (
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
            {item}
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
          <BarChart data={chartData} layout="vertical" margin={{ top: 4, right: 48, left: 4, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" horizontal={false} />
            <XAxis type="number" domain={[90, 100]} stroke="#64748B" fontSize={11} tickLine={false} />
            <YAxis type="category" dataKey="name" stroke="#64748B" fontSize={11} width={96} tickLine={false} />
            <Tooltip
              contentStyle={{
                background: "#111827",
                border: "1px solid #2D3748",
                borderRadius: "12px",
                fontSize: "12px",
              }}
              formatter={(value, _name, item) => {
                const row = item?.payload as CoverageDistributionItem | undefined;
                return [`${Number(value ?? 0).toFixed(1)}% (${row?.sharePct.toFixed(1)}% share)`, "Coverage"];
              }}
            />
            <Bar dataKey="coveragePct" radius={[0, 6, 6, 0]} isAnimationActive>
              {chartData.map((_, index) => (
                <Cell key={`cov-${index}`} fill={index === 0 ? "#7C3AED" : "#8B5CF6"} />
              ))}
              <LabelList
                dataKey="coveragePct"
                position="right"
                formatter={(value) => `${Number(value).toFixed(1)}%`}
                className="fill-[#94A3B8] text-[11px]"
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </motion.div>
    </div>
  );
});
