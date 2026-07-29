"use client";

import { TabLiveShell } from "@/components/platform/TabLiveShell";
import { motion } from "framer-motion";
import {
  AlertOctagon,
  DollarSign,
  Gauge,
  Replace,
  TrendingUp,
  Wrench,
  type LucideIcon,
} from "lucide-react";
import { ArrowUpRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DataTable, PriorityBadge } from "@/components/scan-chain/DataTable";
import { useFilteredMbistData } from "@/hooks/useMbistData";

const iconMap: Record<string, LucideIcon> = {
  wrench: Wrench,
  replace: Replace,
  "alert-octagon": AlertOctagon,
  gauge: Gauge,
  "trending-up": TrendingUp,
  dollar: DollarSign,
};

export function AIRecommendationTab() {
  const liveData = useFilteredMbistData();
  const {aiRecommendations, riskCards } = liveData;

  return (
    <TabLiveShell module="mbist" hookResult={liveData}>
      <div className="dashboard-content">
      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
        {riskCards.map((card, index) => {
          const Icon = iconMap[card.icon] ?? Gauge;
          return (
            <motion.div
              key={card.title}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.06 }}
              className="glass-card gradient-border hover-lift p-5"
            >
              <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-xl bg-[#7C3AED]/15 text-[#7C3AED]">
                <Icon className="h-4 w-4" />
              </div>
              <p className="text-xs text-slate-400">{card.title}</p>
              <p className="mt-1 text-2xl font-bold text-white">{card.value}</p>
              <p className="mt-1 text-xs text-slate-500">{card.subtitle}</p>
            </motion.div>
          );
        })}
      </div>

      <DataTable
        title="AI Recommendations"
        subtitle="Prioritized memory repair and optimization actions"
        data={aiRecommendations}
        rowKey="id"
        searchKeys={["id", "memoryInstance", "recommendation"]}
        searchPlaceholder="Search recommendations..."
        columns={[
          { key: "id", label: "Recommendation ID", render: (row) => <span className="font-mono text-xs text-white">{row.id}</span> },
          { key: "memoryInstance", label: "Memory Instance" },
          { key: "recommendation", label: "Recommendation" },
          { key: "priority", label: "Priority", render: (row) => <PriorityBadge priority={row.priority} /> },
          { key: "confidence", label: "Confidence", render: (row) => `${row.confidence}%` },
          { key: "expectedYieldGain", label: "Expected Yield Gain" },
          {
            key: "action",
            label: "Action",
            sortable: false,
            render: () => (
              <Button variant="ghost" size="sm" className="h-7 text-xs text-[#7C3AED]">
                Apply
                <ArrowUpRight className="ml-1 h-3 w-3" />
              </Button>
            ),
          },
        ]}
      />
      </div>
    </TabLiveShell>
  );
}
