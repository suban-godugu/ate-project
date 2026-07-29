"use client";

import { cn } from "@/lib/utils";
import type { CoverageTimelineStep } from "@/types/scanCoverage";

export function EngineeringTimeline({ steps }: { steps: CoverageTimelineStep[] }) {
  return (
    <div className="flex gap-0 overflow-x-auto pb-2">
      {steps.map((ev, i) => (
        <button
          key={ev.id}
          type="button"
          suppressHydrationWarning
          className="relative flex min-w-[110px] flex-col items-center px-2"
        >
          <div
            className={cn(
              "flex h-9 w-9 items-center justify-center rounded-full border-2 text-[10px] font-bold transition hover:scale-105",
              ev.status === "complete"
                ? "border-emerald-500 bg-emerald-500/20 text-emerald-400"
                : ev.status === "running"
                  ? "border-[#8B5CF6] bg-[#8B5CF6]/20 text-[#A78BFA] animate-pulse"
                  : ev.status === "failed"
                    ? "border-red-500 bg-red-500/20 text-red-400"
                    : "border-[#334155] bg-[#1e293b]/40 text-[#64748B]"
            )}
          >
            {i + 1}
          </div>
          <p className="mt-2 text-center text-[10px] font-medium text-white">{ev.label}</p>
          <p className="text-[9px] text-[#64748B]">{ev.timestamp}</p>
        </button>
      ))}
    </div>
  );
}
