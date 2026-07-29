"use client";

import { motion } from "framer-motion";
import { Download, Search, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { alertWorkflowSteps } from "@/types/alerts";
import type { CriticalAlertSummary, ExecutiveAlertSummary } from "@/types/alerts";

export function CriticalAlertSummaryCard({ data }: { data: CriticalAlertSummary }) {
  const metrics = [
    { label: "Most Critical Issue", value: data.mostCriticalIssue, full: true },
    { label: "Affected Product", value: data.affectedProduct },
    { label: "Affected Tester", value: data.affectedTester },
    { label: "Affected Lot", value: data.affectedLot },
    { label: "Estimated Yield Impact", value: data.estimatedYieldImpact },
    { label: "Estimated Cost Impact", value: data.estimatedCostImpact },
    { label: "Recommended Action", value: data.recommendedAction, full: true },
  ];

  return (
    <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className="glass-card gradient-border hover-lift relative overflow-hidden p-6">
      <div className="pointer-events-none absolute -right-8 -top-8 h-32 w-32 rounded-full bg-red-500/10 blur-2xl" />
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <h3 className="text-base font-semibold text-white">Critical Alert Summary</h3>
          <p className="text-sm text-slate-400">Highest priority issue requiring immediate attention</p>
        </div>
        <Button size="sm" variant="outline" className="rounded-xl border-red-500/30 text-xs text-red-400 hover:border-red-500/50 hover:bg-red-500/10">
          <Search className="mr-1.5 h-3.5 w-3.5" />
          View Root Cause Analysis
        </Button>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {metrics.map((m) => (
          <div key={m.label} className={`rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/40 p-4 ${m.full ? "sm:col-span-2 lg:col-span-3" : ""}`}>
            <p className="text-[10px] uppercase tracking-wider text-slate-500">{m.label}</p>
            <p className={`mt-1 font-semibold text-white ${m.full ? "text-sm" : "text-base"}`}>{m.value}</p>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

export function AlertWorkflowPanel() {
  return (
    <div className="glass-card gradient-border p-6">
      <h3 className="mb-4 text-base font-semibold text-white">Alert Workflow</h3>
      <div className="flex flex-col gap-0 sm:flex-row sm:flex-wrap sm:items-center">
        {alertWorkflowSteps.map((step, i) => (
          <motion.div
            key={step}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08 }}
            className="flex items-center"
          >
            <div className="rounded-xl border border-[#7C3AED]/30 bg-[#7C3AED]/10 px-3 py-2 text-xs font-medium text-white">
              {step}
            </div>
            {i < alertWorkflowSteps.length - 1 && (
              <span className="mx-1 hidden text-[#7C3AED] sm:inline">↓</span>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  );
}

export function ExecutiveAlertSummaryPanel({ data }: { data: ExecutiveAlertSummary }) {
  const metrics = [
    { label: "Critical Alerts", value: data.criticalAlerts },
    { label: "Open Alerts", value: data.openAlerts },
    { label: "Resolved Today", value: data.resolvedToday },
    { label: "Avg Resolution Time", value: data.averageResolutionTime },
    { label: "Estimated Yield Loss", value: data.estimatedYieldLoss },
    { label: "Estimated Cost Impact", value: data.estimatedCostImpact },
    { label: "Top Priority Module", value: data.topPriorityModule },
  ];

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="glass-card gradient-border p-6">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-white">Executive Alert Summary</h3>
          <p className="text-sm text-slate-400">Real-time monitoring across all test modules</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" className="rounded-xl border-[#2D3748] text-xs hover:border-[#7C3AED]">
            <Download className="mr-1.5 h-3.5 w-3.5" />
            Download Alert Report
          </Button>
          <Button size="sm" className="btn-glow rounded-xl bg-[#7C3AED] text-xs hover:bg-[#6D28D9]">
            <Sparkles className="mr-1.5 h-3.5 w-3.5" />
            Generate AI Summary
          </Button>
        </div>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map((m) => (
          <div key={m.label} className="rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/40 p-4">
            <p className="text-[10px] uppercase tracking-wider text-slate-500">{m.label}</p>
            <p className="mt-1 text-lg font-semibold text-white">{m.value}</p>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
