"use client";

import { motion } from "framer-motion";
import { Brain, DollarSign, Layers, Percent, TrendingUp } from "lucide-react";
import type { WaferBottomSummary } from "@/types/wafer";

const items = [
  { key: "totalWafers", label: "Total Wafers", icon: Layers },
  { key: "totalDies", label: "Total Dies", icon: Layers },
  { key: "goodDies", label: "Good Dies", icon: TrendingUp },
  { key: "badDies", label: "Bad Dies", icon: TrendingUp },
  { key: "averageYield", label: "Average Yield", icon: Percent },
  { key: "estimatedSavings", label: "Estimated Savings", icon: DollarSign },
  { key: "aiConfidence", label: "AI Confidence", icon: Brain },
] as const;

export function BottomSummaryBar({ data }: { data: WaferBottomSummary }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card gradient-border grid gap-4 p-5 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7"
    >
      {items.map(({ key, label, icon: Icon }, i) => (
        <div key={key} className="text-center">
          <div className="mx-auto mb-2 flex h-8 w-8 items-center justify-center rounded-lg bg-[#7C3AED]/15 text-[#7C3AED]">
            <Icon className="h-4 w-4" />
          </div>
          <p className="text-[10px] font-medium uppercase tracking-wider text-slate-500">{label}</p>
          <p className="mt-1 text-lg font-bold text-white">{data[key]}</p>
        </div>
      ))}
    </motion.div>
  );
}
