"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

export function AgentWorkflowDiagram({
  steps,
  title = "AI Recommendation Workflow",
  subtitle = "End-to-end recommendation lifecycle",
}: {
  steps: string[];
  title?: string;
  subtitle?: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card gradient-border overflow-x-auto p-6"
    >
      <h3 className="mb-1 text-base font-semibold text-white">{title}</h3>
      <p className="mb-5 text-sm text-slate-400">{subtitle}</p>

      <div className="flex min-w-max items-center gap-1 pb-2">
        {steps.map((step, i) => (
          <motion.div
            key={step}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.06 }}
            className="flex items-center"
          >
            <div className="rounded-xl border border-[#7C3AED]/30 bg-[#7C3AED]/10 px-3 py-2 text-center">
              <p className="whitespace-nowrap text-[11px] font-medium text-white">{step}</p>
            </div>
            {i < steps.length - 1 && (
              <ArrowRight className="mx-1 h-4 w-4 shrink-0 text-[#7C3AED]" />
            )}
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
