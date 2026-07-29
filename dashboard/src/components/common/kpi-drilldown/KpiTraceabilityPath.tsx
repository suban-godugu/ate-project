"use client";

import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import type { KpiTraceabilityNode } from "@/types/kpiDrillDown";

interface KpiTraceabilityPathProps {
  nodes: KpiTraceabilityNode[];
  selectedId?: string | null;
  onSelect?: (node: KpiTraceabilityNode) => void;
}

export function KpiTraceabilityPath({ nodes, selectedId, onSelect }: KpiTraceabilityPathProps) {
  return (
    <div className="overflow-x-auto rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/60 p-4">
      <div className="flex min-w-max items-center gap-1">
        {nodes.map((node, i) => (
          <div key={node.id} className="flex items-center gap-1">
            <button
              type="button"
              suppressHydrationWarning
              onClick={() => onSelect?.(node)}
              className={cn(
                "rounded-lg border px-3 py-2 text-left transition hover:border-[rgba(139,92,246,0.5)]",
                selectedId === node.id
                  ? "border-[#8B5CF6] bg-[#8B5CF6]/15"
                  : "border-[#2D3748]/80 bg-[#121826]/80"
              )}
            >
              <p className="text-[10px] font-bold uppercase tracking-wider text-[#64748B]">{node.label}</p>
              <p className="mt-0.5 text-xs font-semibold text-white">{node.value}</p>
            </button>
            {i < nodes.length - 1 && <ChevronRight className="h-4 w-4 shrink-0 text-[#64748B]" />}
          </div>
        ))}
      </div>
    </div>
  );
}
