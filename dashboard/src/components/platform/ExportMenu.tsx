"use client";

import { useState } from "react";
import { Download, FileSpreadsheet, FileText, Image } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { exportCSV, exportExcel, exportPDF, exportPNG, extractTableData } from "@/lib/exportUtils";
import { getDateRangeLabel } from "@/lib/filterEngine";
import { useFilterStore } from "@/stores/filterStore";
import { useUploadStore } from "@/stores/uploadStore";
import type { ExportFormat } from "@/types/platform";
import { ErrorCard } from "@/components/platform/EmptyState";

interface ExportMenuProps {
  pageTitle: string;
  contentRef: React.RefObject<HTMLElement | null>;
}

export function ExportMenu({ pageTitle, contentRef }: ExportMenuProps) {
  const [error, setError] = useState<string | null>(null);
  const filters = useFilterStore((s) => s.filters);
  const showToast = useUploadStore((s) => s.showToast);

  const runExport = async (format: ExportFormat) => {
    setError(null);
    try {
      const root = contentRef.current;
      const { headers, rows } = extractTableData(root);
      const filterLine = `Filters: ${getDateRangeLabel(filters)} · ${filters.fab} · ${filters.tester} · ${filters.product}`;
      const filenameBase = pageTitle.replace(/\s+/g, "-").toLowerCase();

      switch (format) {
        case "csv":
          exportCSV(`${filenameBase}.csv`, headers.length ? headers : ["Report"], rows.length ? rows : [[filterLine]]);
          break;
        case "excel":
          exportExcel(`${filenameBase}.xls`, headers.length ? headers : ["Report"], rows.length ? rows : [[filterLine]]);
          break;
        case "pdf":
          exportPDF(pageTitle, [filterLine, "", ...(rows.flat().length ? rows.map((r) => r.join(" | ")) : ["Dashboard export snapshot"])]);
          break;
        case "png":
          await exportPNG(root, `${filenameBase}.png`);
          break;
      }
      showToast(`${format.toUpperCase()} export started`, "success");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Export failed";
      setError(message);
      showToast(message, "error");
    }
  };

  return (
    <div className="relative">
      <DropdownMenu>
        <DropdownMenuTrigger
          className="hidden rounded-xl border border-[#2D3748] px-3 py-2 text-[11px] text-white hover:border-[#7C3AED] lg:inline-flex lg:items-center"
          aria-label="Export report"
        >
          <Download className="mr-1.5 h-3.5 w-3.5" />
          Export Report
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="border-[#2D3748] bg-[#111827]">
          <DropdownMenuGroup>
            <DropdownMenuLabel className="text-slate-400">Export Format</DropdownMenuLabel>
            <DropdownMenuItem onClick={() => runExport("pdf")}>
              <FileText className="mr-2 h-4 w-4" /> PDF
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => runExport("excel")}>
              <FileSpreadsheet className="mr-2 h-4 w-4" /> Excel
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => runExport("csv")}>
              <FileText className="mr-2 h-4 w-4" /> CSV
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => runExport("png")}>
              <Image className="mr-2 h-4 w-4" /> PNG Screenshot
            </DropdownMenuItem>
          </DropdownMenuGroup>
        </DropdownMenuContent>
      </DropdownMenu>
      {error && (
        <div className="absolute right-0 top-full z-50 mt-2 w-72">
          <ErrorCard message={error} onRetry={() => setError(null)} />
        </div>
      )}
    </div>
  );
}
