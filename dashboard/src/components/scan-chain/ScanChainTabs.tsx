"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import type { ScanChainTab } from "@/types/scanChain";

const tabs: { id: ScanChainTab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "pattern-analysis", label: "Pattern Analysis" },
  { id: "failure-analysis", label: "Failure Analysis" },
  { id: "scan-diagnosis", label: "Scan Diagnosis" },
];

interface ScanChainTabsProps {
  activeTab: ScanChainTab;
  onTabChange: (tab: ScanChainTab) => void;
}

export function ScanChainTabs({ activeTab, onTabChange }: ScanChainTabsProps) {
  return (
    <nav className="scan-chain-tabs flex gap-1 border-b border-[#2D3748]/60">
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            type="button"
            onClick={() => onTabChange(tab.id)}
            className={cn(
              "relative px-4 py-3 text-sm transition-colors duration-200",
              isActive
                ? "font-semibold text-white"
                : "font-medium text-slate-400 hover:text-slate-200"
            )}
          >
            {tab.label}
            {isActive && (
              <motion.div
                layoutId="scan-chain-tab-indicator"
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
