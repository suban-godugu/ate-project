"use client";

import { motion } from "framer-motion";
import { BrainCircuit, Bug, Gauge } from "lucide-react";
import { cn } from "@/lib/utils";
import type { RecommendationAgentTab } from "@/types/recommendation";

const tabs: {
  id: RecommendationAgentTab;
  label: string;
  subtitle: string;
  icon: typeof BrainCircuit;
}[] = [
  {
    id: "pattern-agent",
    label: "Pattern Recommendation Agent",
    subtitle: "ATPG Pattern Optimization",
    icon: BrainCircuit,
  },
  {
    id: "scan-debug-agent",
    label: "Scan Debug Recommendation Agent",
    subtitle: "Failure Diagnosis & Debug",
    icon: Bug,
  },
  {
    id: "test-optimization-agent",
    label: "Test Optimization Recommendation Agent",
    subtitle: "Yield, Cost & Test Optimization",
    icon: Gauge,
  },
];

interface AgentTabsProps {
  activeTab: RecommendationAgentTab;
  onTabChange: (tab: RecommendationAgentTab) => void;
}

export function AgentTabs({ activeTab, onTabChange }: AgentTabsProps) {
  return (
    <nav className="flex gap-1 overflow-x-auto border-b border-[#2D3748]/60">
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        const Icon = tab.icon;
        return (
          <button
            key={tab.id}
            type="button"
            onClick={() => onTabChange(tab.id)}
            className={cn(
              "relative shrink-0 px-4 py-3 text-left transition-colors duration-200",
              isActive
                ? "text-white"
                : "text-slate-400 hover:text-slate-200"
            )}
          >
            <div className="flex items-center gap-2">
              <Icon
                className={cn(
                  "h-4 w-4",
                  isActive ? "text-[#7C3AED]" : "text-slate-500"
                )}
              />
              <div>
                <p className={cn("text-sm", isActive ? "font-semibold" : "font-medium")}>
                  {tab.label}
                </p>
                <p className="text-[10px] text-slate-500">{tab.subtitle}</p>
              </div>
            </div>
            {isActive && (
              <motion.div
                layoutId="rec-agent-tab-indicator"
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
