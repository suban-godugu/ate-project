import { isLiveApi } from "@/lib/api/config";
import { actionsApi } from "@/lib/api/actions";

export function downloadBlob(content: string | Blob, filename: string, mime: string) {
  const blob = content instanceof Blob ? content : new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export function exportCSV(filename: string, headers: string[], rows: string[][]) {
  const csv = [headers, ...rows]
    .map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(","))
    .join("\n");
  downloadBlob(csv, filename, "text/csv;charset=utf-8;");
}

export function exportExcel(filename: string, headers: string[], rows: string[][]) {
  const csv = [headers, ...rows]
    .map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join("\t"))
    .join("\n");
  downloadBlob(csv, filename.replace(/\.csv$/, ".xls"), "application/vnd.ms-excel");
}

export async function exportPDF(title: string, lines: string[]) {
  if (isLiveApi()) {
    const url = await actionsApi.exportPDF(title, lines);
    window.open(url, "_blank");
    return;
  }
  const content = [
    title,
    `Generated: ${new Date().toLocaleString()}`,
    "",
    ...lines,
  ].join("\n");
  downloadBlob(content, `${title.replace(/\s+/g, "-").toLowerCase()}.pdf`, "application/pdf");
}

export async function exportPNG(element: HTMLElement | null, filename: string) {
  if (!element) throw new Error("No content to capture");
  const html2canvas = (await import("html2canvas")).default;
  const canvas = await html2canvas(element, {
    backgroundColor: "#090B12",
    scale: 2,
  });
  canvas.toBlob((blob) => {
    if (!blob) throw new Error("Failed to capture screenshot");
    downloadBlob(blob, filename, "image/png");
  });
}

export function extractTableData(root: HTMLElement | null): {
  headers: string[];
  rows: string[][];
} {
  if (!root) return { headers: [], rows: [] };
  const table = root.querySelector("table");
  if (!table) {
    return {
      headers: ["Section", "Content"],
      rows: [[root.dataset.exportTitle ?? "Dashboard", root.innerText.slice(0, 500)]],
    };
  }
  const headers = Array.from(table.querySelectorAll("thead th")).map((th) => th.textContent?.trim() ?? "");
  const rows = Array.from(table.querySelectorAll("tbody tr")).map((tr) =>
    Array.from(tr.querySelectorAll("td")).map((td) => td.textContent?.trim() ?? "")
  );
  return { headers, rows };
}
