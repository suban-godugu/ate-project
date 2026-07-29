"use client";

import { motion } from "framer-motion";
import type { WaferInfoPanelData } from "@/types/wafer";

export function WaferInfoPanel({ data }: { data: WaferInfoPanelData }) {
  const fields = [
    { label: "Defect Type", value: data.defectType },
    { label: "Assigned Lot", value: data.assignedLot },
    { label: "Confidence", value: `${data.confidence}%` },
    { label: "Good Dies", value: data.goodDies.toLocaleString() },
    { label: "Bad Dies", value: data.badDies.toLocaleString() },
    { label: "Total Dies", value: data.totalDies.toLocaleString() },
    { label: "Yield", value: `${data.yield}%` },
    { label: "Average Cost", value: data.averageCost },
    { label: "Recommendation", value: data.recommendation, wide: true },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, x: 12 }}
      animate={{ opacity: 1, x: 0 }}
      className="glass-card gradient-border h-full p-5"
    >
      <h3 className="mb-1 text-base font-semibold text-white">Analysis Information</h3>
      <p className="mb-4 text-sm text-slate-400">Current wafer classification summary</p>
      <div className="grid gap-3 sm:grid-cols-2">
        {fields.map((f) => (
          <div
            key={f.label}
            className={`rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/40 p-3 ${f.wide ? "sm:col-span-2" : ""}`}
          >
            <p className="text-[10px] font-medium uppercase tracking-wider text-slate-500">{f.label}</p>
            <p className={`mt-1 font-semibold text-white ${f.wide ? "text-sm leading-relaxed" : ""}`}>{f.value}</p>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
