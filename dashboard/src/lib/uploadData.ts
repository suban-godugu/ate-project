import type { AILogSummary, DataUploadRecord, LogUploadRecord } from "@/types/upload";

export const initialDataUploadHistory: DataUploadRecord[] = [
  { id: "UPL-D-001", fileName: "scan_chain_lot4821.csv", module: "Scan Chain Analysis", fileType: "CSV", size: "24.8 MB", uploadedBy: "J. Park", uploadTime: "Jun 29, 2026 · 09:12", status: "Completed" },
  { id: "UPL-D-002", fileName: "mbist_bank_results.xlsx", module: "MBIST Analysis", fileType: "XLSX", size: "18.2 MB", uploadedBy: "M. Chen", uploadTime: "Jun 29, 2026 · 08:45", status: "Completed" },
  { id: "UPL-D-003", fileName: "wafer_yield_batch.json", module: "Wafer Analysis", fileType: "JSON", size: "6.4 MB", uploadedBy: "S. Patel", uploadTime: "Jun 28, 2026 · 16:30", status: "Processing" },
  { id: "UPL-D-004", fileName: "cost_intel_q2.zip", module: "Cost Intelligence", fileType: "ZIP", size: "142 MB", uploadedBy: "R. Singh", uploadTime: "Jun 28, 2026 · 14:08", status: "Failed" },
];

export const initialLogUploadHistory: LogUploadRecord[] = [
  { id: "UPL-L-001", fileName: "lot4821_scan.stdf", module: "Scan Chain", tester: "V93000", lotId: "LOT-4821", waferId: "W-12", fileType: "STDF", size: "1.2 GB", uploadTime: "Jun 29, 2026 · 10:05", status: "Completed", processingTime: "4m 12s", uploadedBy: "J. Park" },
  { id: "UPL-L-002", fileName: "mbist_repair.log", module: "MBIST", tester: "UltraFlex", lotId: "LOT-3105", waferId: "W-22", fileType: "LOG", size: "842 MB", uploadTime: "Jun 29, 2026 · 09:40", status: "Parsing", processingTime: "—", uploadedBy: "M. Chen" },
  { id: "UPL-L-003", fileName: "lbist_misr.stil", module: "LBIST", tester: "J750", lotId: "LOT-2441", waferId: "W-04", fileType: "STIL", size: "520 MB", uploadTime: "Jun 28, 2026 · 18:22", status: "Completed", processingTime: "2m 48s", uploadedBy: "A. Kim" },
  { id: "UPL-L-004", fileName: "wafer_map.xml", module: "Wafer Analysis", tester: "T2000", lotId: "LOT-7892", waferId: "W-08", fileType: "XML", size: "96 MB", uploadTime: "Jun 28, 2026 · 11:15", status: "Queued", processingTime: "—", uploadedBy: "S. Patel" },
];

export const defaultAILogSummary: AILogSummary = {
  filesProcessed: "1",
  patternsFound: "42",
  scanChains: "18",
  memoryBlocks: "12",
  logicBlocks: "8",
  waferCount: "25",
  defectsFound: "148",
  yield: "92.4%",
  estimatedTestCost: "$42,800",
  estimatedSavings: "$8,200",
};

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / 1024 ** i).toFixed(i > 1 ? 1 : 0)} ${units[i]}`;
}

export function getFileExtension(name: string): string {
  const idx = name.lastIndexOf(".");
  return idx >= 0 ? name.slice(idx).toLowerCase() : "";
}

export function generateUploadId(prefix: "D" | "L"): string {
  return `UPL-${prefix}-${Date.now().toString().slice(-6)}`;
}

export function formatNow(): string {
  return new Date().toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Format API ISO timestamps for display; pass through mock strings unchanged. */
export function formatUploadTime(value: string): string {
  if (!value || !value.includes("T")) return value;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
