"use client";

import { motion } from "framer-motion";
import { Bot } from "lucide-react";
import type { AgentMeta } from "@/types/recommendation";
import type { ReactNode } from "react";

interface AgentSectionCardProps {
  meta: AgentMeta;
  children: ReactNode;
  delay?: number;
}

export function AgentSectionCard({ meta, children, delay = 0 }: AgentSectionCardProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4 }}
      className="glass-card gradient-border overflow-hidden p-6 sm:p-8"
    >
      <div className="mb-6 flex flex-wrap items-start gap-4">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-[#7C3AED]/20 text-[#7C3AED]">
          <Bot className="h-6 w-6" />
        </div>
        <div className="min-w-0 flex-1">
          <h2 className="text-lg font-bold text-white sm:text-xl">{meta.title}</h2>
          <div className="mt-4 grid gap-4 lg:grid-cols-3">
            <div>
              <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-[#7C3AED]">
                Responsibilities
              </p>
              <ul className="space-y-1">
                {meta.responsibilities.map((item) => (
                  <li key={item} className="flex items-start gap-2 text-xs text-slate-300">
                    <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-[#7C3AED]" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-cyan-400">
                Inputs
              </p>
              <ul className="space-y-1">
                {meta.inputs.map((item) => (
                  <li key={item} className="text-xs text-slate-400">
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-emerald-400">
                Outputs
              </p>
              <ul className="space-y-1">
                {meta.outputs.map((item) => (
                  <li key={item} className="text-xs text-slate-300">
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
      {children}
    </motion.section>
  );
}
