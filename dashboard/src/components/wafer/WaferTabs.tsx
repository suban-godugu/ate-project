"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { useFilteredWaferData } from "@/hooks/useWaferData";
import type { WaferTab } from "@/types/wafer";
import { cn } from "@/lib/utils";

interface WaferTabsProps {
  activeTab: WaferTab;
  onTabChange: (tab: WaferTab) => void;
}

export function WaferTabs({ activeTab, onTabChange }: WaferTabsProps) {
  const { WAFER_DEFECT_CLASSES, defectClassMeta } = useFilteredWaferData();

  const tabs = useMemo(
    (): { id: WaferTab; label: string }[] => [
      { id: "overview", label: "Overview" },
      ...WAFER_DEFECT_CLASSES.map((id) => ({
        id,
        label: defectClassMeta[id].tabLabel,
      })),
    ],
    [WAFER_DEFECT_CLASSES, defectClassMeta]
  );

  return (
    <nav
      className="flex gap-1 overflow-x-auto border-b border-[#2D3748]/60 pb-px scrollbar-thin"
      role="tablist"
      aria-label="Wafer analysis tabs"
    >
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={isActive}
            onClick={() => onTabChange(tab.id)}
            className={cn(
              "relative shrink-0 px-4 py-3 text-sm transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#7C3AED]/50",
              isActive
                ? "font-semibold text-white"
                : "font-medium text-slate-400 hover:text-slate-200"
            )}
          >
            {tab.label}
            {isActive && (
              <motion.div
                layoutId="wafer-tab-underline"
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
