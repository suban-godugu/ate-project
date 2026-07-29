import type { ExportRow } from "@/utils/batchAggregates";

export function downloadTextFile(
  filename: string,
  content: string,
  mime: string,
): void {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function exportRowsToCsv(rows: ExportRow[]): string {
  const headers = [
    "Wafer Name",
    "Defect",
    "LOT",
    "Yield",
    "Confidence",
    "Good Dies",
    "Fail Dies",
    "Total Dies",
  ];
  const lines = [
    headers.join(","),
    ...rows.map((row) =>
      [
        csvEscape(row.wafer_name),
        csvEscape(row.defect),
        csvEscape(row.lot),
        row.yield ?? "",
        row.confidence ?? "",
        row.good_dies ?? "",
        row.fail_dies ?? "",
        row.total_dies ?? "",
      ].join(","),
    ),
  ];
  return lines.join("\n");
}

function csvEscape(value: string): string {
  if (/[",\n]/.test(value)) return `"${value.replace(/"/g, '""')}"`;
  return value;
}

export function exportSessionCsv(rows: ExportRow[]): void {
  const stamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-");
  downloadTextFile(
    `wafervision-batch-${stamp}.csv`,
    exportRowsToCsv(rows),
    "text/csv;charset=utf-8",
  );
}

export function exportSessionJson(payload: unknown): void {
  const stamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-");
  downloadTextFile(
    `wafervision-batch-${stamp}.json`,
    JSON.stringify(payload, null, 2),
    "application/json;charset=utf-8",
  );
}
