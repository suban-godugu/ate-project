"use client";

import { cn } from "@/lib/utils";

export function Progress({ value, className }: { value: number; className?: string }) {
  return (
    <div className={cn("h-2 w-full overflow-hidden rounded-full bg-[#0A1020]", className)}>
      <div
        className="h-full rounded-full bg-gradient-to-r from-[#7C3AED] to-[#8B5CF6] transition-all duration-300"
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  );
}
