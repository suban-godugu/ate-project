"use client";

import { motion } from "framer-motion";
import { Check, Circle, Loader } from "lucide-react";
import type { WorkflowStep } from "@/types/kpiDrillDown";

export function EngineeringWorkflow({ steps }: { steps: WorkflowStep[] }) {
  return (
    <section className="glass-card gradient-border p-4">
      <div className="mb-4">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Debug Pipeline</div>
        <h2 className="font-display text-lg font-semibold text-white">Failure Logs → Validation</h2>
      </div>
      <div className="flex flex-col gap-3 overflow-x-auto md:flex-row md:items-center md:gap-0">
        {steps.map((step, idx) => (
          <div key={step.id} className="flex items-center md:min-w-0 md:flex-1">
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
              className={`flex w-full items-center gap-2 rounded-xl border px-3 py-2 ${
                step.status === "done"
                  ? "border-success/30 bg-success/10"
                  : step.status === "active"
                    ? "border-primary/40 bg-primary/15"
                    : "border-border/70 bg-white/5"
              }`}
            >
              {step.status === "done" ? (
                <Check size={14} className="text-success" />
              ) : step.status === "active" ? (
                <Loader size={14} className="animate-spin text-primary" />
              ) : (
                <Circle size={14} className="text-slate-500" />
              )}
              <span className="text-xs text-slate-200">{step.label}</span>
            </motion.div>
            {idx < steps.length - 1 ? (
              <div className="mx-1 hidden h-px w-4 bg-border md:block" />
            ) : null}
          </div>
        ))}
      </div>
    </section>
  );
}
