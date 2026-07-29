"use client";

import { memo, useState } from "react";
import { Download, FileJson } from "lucide-react";
import type { ExportFormat } from "@/stores/reportStore";
import { useReportStore } from "@/stores/reportStore";
import { notify } from "@/stores/toastStore";
import {
  ensureReportForUpload,
  evaluationExportUrl,
  exportReportFile,
  reportDownloadUrl,
} from "@/services/reports";

const FORMATS: ExportFormat[] = ["pdf", "csv", "xlsx", "json", "html"];

type Props = {
  uploadId?: string | null;
  executionId?: string | null;
  reportId?: string | null;
};

export const ReportsExportPanel = memo(function ReportsExportPanel({
  uploadId,
  executionId,
  reportId: initialReportId,
}: Props) {
  const [busy, setBusy] = useState<ExportFormat | null>(null);
  const setReportId = useReportStore((s) => s.setReportId);
  const setExporting = useReportStore((s) => s.setExporting);

  async function download(format: ExportFormat) {
    if (!uploadId && !executionId) return;
    setBusy(format);
    setExporting(format);
    try {
      let reportId = initialReportId || useReportStore.getState().reportId;
      if (!reportId && uploadId) {
        reportId = await ensureReportForUpload(uploadId);
        setReportId(reportId);
      }
      let url: string;
      if (reportId) {
        url = await exportReportFile(reportId, format);
        if (!url.startsWith("http") && !url.startsWith("/")) {
          url = reportDownloadUrl(reportId, format);
        }
      } else if (executionId) {
        const evalFmt = format === "xlsx" ? "excel" : format;
        url = await evaluationExportUrl(executionId, evalFmt);
      } else {
        throw new Error("No report or execution context");
      }
      window.open(url, "_blank", "noopener,noreferrer");
      notify({
        title: "Report Generated",
        description: `${format.toUpperCase()} export ready for download.`,
        variant: "success",
      });
    } catch (err) {
      notify({
        title: "Export Failed",
        description: err instanceof Error ? err.message : "Could not export report",
        variant: "error",
      });
    } finally {
      setBusy(null);
      setExporting(null);
    }
  }

  return (
    <div className="glass-panel rounded-2xl p-4" data-testid="reports-export">
      <div className="mb-3 flex items-center gap-2">
        <FileJson size={16} className="text-[var(--accent)]" />
        <h3 className="text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
          Reports Export
        </h3>
      </div>
      <div className="flex flex-wrap gap-2">
        {FORMATS.map((fmt) => (
          <button
            key={fmt}
            type="button"
            disabled={Boolean(busy) || (!uploadId && !executionId)}
            onClick={() => download(fmt)}
            className="inline-flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs font-medium hover:bg-white/10 disabled:opacity-40"
          >
            <Download size={14} />
            {busy === fmt ? "Exporting…" : fmt.toUpperCase()}
          </button>
        ))}
      </div>
    </div>
  );
});
