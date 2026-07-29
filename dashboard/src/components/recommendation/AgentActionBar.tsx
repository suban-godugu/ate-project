"use client";

import {
  Download,
  FileSpreadsheet,
  FileText,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useUploadStore } from "@/stores/uploadStore";

type AgentActionVariant = "scan-debug" | "test-opt" | "default";

interface AgentActionBarProps {
  variant?: AgentActionVariant;
}

export function AgentActionBar({ variant = "default" }: AgentActionBarProps) {
  const showToast = useUploadStore((s) => s.showToast);

  const applyLabel =
    variant === "test-opt" ? "Apply Optimization" : "Apply Recommendation";
  const reportLabel =
    variant === "scan-debug"
      ? "Generate Debug Report"
      : variant === "test-opt"
        ? "Generate Optimization Report"
        : "Generate ATPG Script";

  return (
    <div className="glass-card gradient-border flex flex-wrap gap-2 p-4">
      <Button
        size="sm"
        onClick={() => showToast("Recommendation approved", "success")}
        className="rounded-xl bg-emerald-600 text-xs hover:bg-emerald-700"
      >
        <ThumbsUp className="mr-1.5 h-3.5 w-3.5" />
        Approve Recommendation
      </Button>
      <Button
        size="sm"
        variant="outline"
        onClick={() => showToast("Recommendation rejected", "info")}
        className="rounded-xl border-[#2D3748] text-xs hover:border-red-500/50 hover:text-red-400"
      >
        <ThumbsDown className="mr-1.5 h-3.5 w-3.5" />
        Reject Recommendation
      </Button>
      <Button
        size="sm"
        variant="outline"
        onClick={() => showToast("Applying recommendation...", "info")}
        className="rounded-xl border-[#2D3748] text-xs hover:border-[#7C3AED]"
      >
        {applyLabel}
      </Button>
      <Button
        size="sm"
        variant="outline"
        onClick={() => showToast("PDF export started", "success")}
        className="rounded-xl border-[#2D3748] text-xs hover:border-[#7C3AED]"
      >
        <FileText className="mr-1.5 h-3.5 w-3.5" />
        Export PDF
      </Button>
      <Button
        size="sm"
        variant="outline"
        onClick={() => showToast("Excel export started", "success")}
        className="rounded-xl border-[#2D3748] text-xs hover:border-[#7C3AED]"
      >
        <FileSpreadsheet className="mr-1.5 h-3.5 w-3.5" />
        Export Excel
      </Button>
      <Button
        size="sm"
        onClick={() => showToast(`${reportLabel} started`, "info")}
        className="btn-glow rounded-xl bg-[#7C3AED] text-xs hover:bg-[#6D28D9]"
      >
        <Sparkles className="mr-1.5 h-3.5 w-3.5" />
        {reportLabel}
      </Button>
      {variant === "default" && (
        <Button
          size="sm"
          variant="outline"
          onClick={() => showToast("Report export started", "success")}
          className="rounded-xl border-[#2D3748] text-xs hover:border-[#7C3AED]"
        >
          <Download className="mr-1.5 h-3.5 w-3.5" />
          Export Report
        </Button>
      )}
    </div>
  );
}
