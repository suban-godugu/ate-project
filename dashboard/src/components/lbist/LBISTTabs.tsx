"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import type { LbistTab } from "@/types/lbist";

const tabs: { id: LbistTab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "coverage-analysis", label: "Coverage Analysis" },
  { id: "failure-analysis", label: "Failure Analysis" },
  { id: "diagnosis", label: "Diagnosis" },
  { id: "ai-recommendation", label: "AI Recommendation" },
];

export function LBISTTabs({ activeTab, onTabChange }: { activeTab: LbistTab; onTabChange: (tab: LbistTab) => void }) {
  return (
    <nav className="flex gap-1 overflow-x-auto border-b border-[#2D3748]/60">
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            type="button"
            onClick={() => onTabChange(tab.id)}
            className={cn(
              "relative shrink-0 px-4 py-3 text-sm transition-colors duration-200",
              isActive ? "font-semibold text-white" : "font-medium text-slate-400 hover:text-slate-200"
            )}
          >
            {tab.label}
            {isActive && (
              <motion.div
                layoutId="lbist-tab-indicator"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#7C3AED]"
                style={{ boxShadow: "0 0 12px rgba(124, 58, 237, 0.6)" }}
                transition={{ type: "spring", stiffness: 400, damping: 30 }}
              />
            )}
          </button>
        );
      })}
    </nav>
  );
}
