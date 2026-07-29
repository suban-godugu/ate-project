"use client";

import {
  CheckCircle,
  FileSpreadsheet,
  FileText,
  Network,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useUploadStore } from "@/stores/uploadStore";

export function ScanDiagnosisActionBar() {
  const showToast = useUploadStore((s) => s.showToast);

  return (
    <div className="glass-card gradient-border flex flex-wrap gap-2 p-4">
      <Button
        size="sm"
        variant="outline"
        onClick={() => showToast("Topology viewer focused", "info")}
        className="rounded-xl border-[#2D3748] text-xs hover:border-[#7C3AED]"
      >
        <Network className="mr-1.5 h-3.5 w-3.5" />
        View Topology
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
        onClick={() => showToast("Debug report generation started", "info")}
        className="btn-glow rounded-xl bg-[#7C3AED] text-xs hover:bg-[#6D28D9]"
      >
        <Sparkles className="mr-1.5 h-3.5 w-3.5" />
        Generate Debug Report
      </Button>
      <Button
        size="sm"
        onClick={() => showToast("Diagnosis approved", "success")}
        className="rounded-xl bg-emerald-600 text-xs hover:bg-emerald-700"
      >
        <CheckCircle className="mr-1.5 h-3.5 w-3.5" />
        Approve Diagnosis
      </Button>
    </div>
  );
}
