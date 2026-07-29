"use client";

import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";

interface AgentTabHeaderProps {
  title: string;
  description: string;
  icon: LucideIcon;
}

export function AgentTabHeader({ title, description, icon: Icon }: AgentTabHeaderProps) {
  return (
    <motion.header
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card gradient-border p-5 sm:p-6"
    >
      <div className="flex items-start gap-4">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[#7C3AED]/20 text-[#7C3AED]">
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-white sm:text-xl">{title}</h2>
          <p className="mt-1 max-w-3xl text-sm text-slate-400">{description}</p>
        </div>
      </div>
    </motion.header>
  );
}
