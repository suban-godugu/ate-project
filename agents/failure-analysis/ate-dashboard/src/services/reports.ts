import { exportReport, generateReport, listReports } from "@/lib/api";
import { appConfig } from "@/lib/config";
import type { ExportFormat } from "@/stores/reportStore";

const FORMAT_MAP: Record<ExportFormat, "pdf" | "csv" | "xlsx" | "json" | "html"> = {
  pdf: "pdf",
  csv: "csv",
  xlsx: "xlsx",
  json: "json",
  html: "html",
};

export async function ensureReportForUpload(uploadId: string) {
  const existing = await listReports({ limit: 20 });
  const match = existing.reports.find((r) => r.upload_id === uploadId);
  if (match?.report_id) return match.report_id;
  const created = await generateReport({ upload_id: uploadId, legacy: true });
  return created.report_id;
}

export function reportDownloadUrl(reportId: string, format: ExportFormat) {
  const fmt = format === "xlsx" ? "excel" : format;
  return `${appConfig.apiBaseUrl}/reports/download/${fmt}?report_id=${encodeURIComponent(reportId)}`;
}

export async function exportReportFile(reportId: string, format: ExportFormat) {
  const mapped = FORMAT_MAP[format];
  const result = await exportReport({ report_id: reportId, format: mapped });
  if (result.download_url) return result.download_url;
  return reportDownloadUrl(reportId, format);
}

export async function evaluationExportUrl(executionId: string, format: string) {
  return `${appConfig.apiBaseUrl}/evaluation/download/${format}?execution_id=${encodeURIComponent(executionId)}`;
}
