"use client";

import { motion } from "framer-motion";
import { Download, Search, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useUploadStore } from "@/stores/uploadStore";

interface ScanDiagnosisTabHeaderProps {
  onRunDiagnosis: () => void;
  isRunning?: boolean;
}

export function ScanDiagnosisTabHeader({
  onRunDiagnosis,
  isRunning = false,
}: ScanDiagnosisTabHeaderProps) {
  const showToast = useUploadStore((s) => s.showToast);

  return (
    <motion.header
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card gradient-border p-5 sm:p-6"
    >
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex items-start gap-4">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[#7C3AED]/20 text-[#7C3AED]">
            <Search className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white sm:text-xl">Scan Diagnosis</h2>
            <p className="mt-1 max-w-3xl text-sm text-slate-400">
              AI-powered scan chain diagnosis, failure localization, topology analysis, and debug
              reporting.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            onClick={onRunDiagnosis}
            disabled={isRunning}
            className="btn-glow rounded-xl bg-[#7C3AED] text-xs hover:bg-[#6D28D9]"
          >
            <Search className="mr-1.5 h-3.5 w-3.5" />
            {isRunning ? "Running..." : "Run AI Diagnosis"}
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => showToast("Diagnosis report export started", "success")}
            className="rounded-xl border-[#2D3748] text-xs hover:border-[#7C3AED]"
          >
            <Download className="mr-1.5 h-3.5 w-3.5" />
            Export Diagnosis Report
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => showToast("Upload diagnosis logs dialog opened", "info")}
            className="rounded-xl border-[#2D3748] text-xs hover:border-[#7C3AED]"
          >
            <Upload className="mr-1.5 h-3.5 w-3.5" />
            Upload Diagnosis Logs
          </Button>
        </div>
      </div>
    </motion.header>
  );
}
