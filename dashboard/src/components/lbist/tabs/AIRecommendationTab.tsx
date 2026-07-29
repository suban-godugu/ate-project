"use client";

import { TabLiveShell } from "@/components/platform/TabLiveShell";
import { motion } from "framer-motion";
import {
  DollarSign,
  Gauge,
  Target,
  Timer,
  TrendingUp,
  Wrench,
  Zap,
  type LucideIcon,
} from "lucide-react";
import { ArrowUpRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DataTable, PriorityBadge } from "@/components/scan-chain/DataTable";
import { useFilteredLbistData } from "@/hooks/useLbistData";

const iconMap: Record<string, LucideIcon> = {
  target: Target,
  zap: Zap,
  wrench: Wrench,
  gauge: Gauge,
  "trending-up": TrendingUp,
  timer: Timer,
  dollar: DollarSign,
};

export function AIRecommendationTab() {
  const liveData = useFilteredLbistData();
  const {aiRecommendations, riskCards } = liveData;

  return (
    <TabLiveShell module="lbist" hookResult={liveData}>
      <div className="dashboard-content">
      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
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
        subtitle="Prioritized LBIST optimization and repair actions"
        data={aiRecommendations}
        rowKey="id"
        searchKeys={["id", "logicBlock", "recommendation"]}
        searchPlaceholder="Search recommendations..."
        columns={[
          { key: "id", label: "Recommendation ID", render: (row) => <span className="font-mono text-xs text-white">{row.id}</span> },
          { key: "logicBlock", label: "Logic Block" },
          { key: "recommendation", label: "Recommendation" },
          { key: "priority", label: "Priority", render: (row) => <PriorityBadge priority={row.priority} /> },
          { key: "confidence", label: "Confidence", render: (row) => `${row.confidence}%` },
          { key: "expectedBenefit", label: "Expected Benefit" },
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
