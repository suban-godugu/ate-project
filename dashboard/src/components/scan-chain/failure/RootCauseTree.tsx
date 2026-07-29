"use client";

import { motion } from "framer-motion";
import { ChevronRight } from "lucide-react";
import type { RootCauseTreeNode } from "@/types/scanChain";

function TreeNode({ node, depth = 0 }: { node: RootCauseTreeNode; depth?: number }) {
  return (
    <div className={depth > 0 ? "ml-4 border-l border-[#2D3748] pl-4" : ""}>
      <motion.div
        initial={{ opacity: 0, x: -8 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: depth * 0.08 }}
        className="mb-3 rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/50 p-3"
      >
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            {depth > 0 && <ChevronRight className="h-3 w-3 text-[#7C3AED]" />}
            <p className="text-sm font-medium text-white">{node.cause}</p>
          </div>
          <span className="rounded-full bg-[#7C3AED]/15 px-2 py-0.5 text-[10px] font-medium text-[#7C3AED]">
            {node.confidence}% confidence
          </span>
        </div>
        <p className="mt-1 text-[11px] text-slate-500">
          {node.affectedPatterns.toLocaleString()} affected patterns
        </p>
      </motion.div>
      {node.children?.map((child) => (
        <TreeNode key={child.id} node={child} depth={depth + 1} />
      ))}
    </div>
  );
}

export function RootCauseTree({ nodes }: { nodes: RootCauseTreeNode[] }) {
  return (
    <div className="glass-card gradient-border overflow-hidden p-6">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-white">Root Cause Analysis</h3>
        <p className="text-sm text-slate-400">Top predicted causes with confidence and affected patterns</p>
      </div>
      <div className="max-h-[320px] space-y-2 overflow-y-auto pr-1">
        {nodes.map((node) => (
          <TreeNode key={node.id} node={node} />
        ))}
      </div>
    </div>
  );
}
