"use client";

import { Badge } from "@/components/ui/badge";
import type { Priority } from "@/types/recommendation";

const styles: Record<Priority, string> = {
  Critical: "bg-red-500/15 text-red-400 border-red-500/30",
  High: "bg-orange-500/15 text-orange-400 border-orange-500/30",
  Medium: "bg-yellow-500/15 text-yellow-400 border-yellow-500/30",
  Low: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
};

export function PriorityBadge({ priority }: { priority: Priority | string }) {
  const style = styles[priority as Priority] ?? styles.Medium;
  return (
    <Badge variant="outline" className={`border ${style}`}>
      {priority}
    </Badge>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const variant =
    status === "Implemented" || status === "Approved"
      ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"
      : status === "In Review"
        ? "bg-cyan-500/15 text-cyan-400 border-cyan-500/30"
        : "bg-amber-500/15 text-amber-400 border-amber-500/30";
  return (
    <Badge variant="outline" className={`border ${variant}`}>
      {status}
    </Badge>
  );
}

export function ModuleBadge({ module }: { module: string }) {
  const colors: Record<string, string> = {
    "Scan Chain": "bg-purple-500/15 text-purple-400 border-purple-500/30",
    MBIST: "bg-cyan-500/15 text-cyan-400 border-cyan-500/30",
    LBIST: "bg-orange-500/15 text-orange-400 border-orange-500/30",
    Wafer: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  };
  return (
    <Badge variant="outline" className={`border ${colors[module] ?? "bg-slate-500/15 text-slate-400 border-slate-500/30"}`}>
      {module}
    </Badge>
  );
}
