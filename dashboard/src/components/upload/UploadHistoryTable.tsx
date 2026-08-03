"use client";

import { useMemo, useState } from "react";
import { Download, Eye, RefreshCw, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useDataUploadHistory, useInvalidateUploadHistory, useLogUploadHistory } from "@/hooks/useUploadHistory";
import { isLiveApi } from "@/lib/api/config";
import { uploadsApi } from "@/lib/api/uploads";
import { downloadBlob } from "@/lib/exportUtils";
import { formatUploadTime } from "@/lib/uploadData";
import { useUpload } from "@/contexts/UploadContext";
import type { DataUploadRecord, LogUploadRecord, UploadStatus } from "@/types/upload";

const statusStyles: Record<UploadStatus, string> = {
  Queued: "bg-orange-500/15 text-orange-400 border-orange-500/30",
  Uploading: "bg-cyan-500/15 text-cyan-400 border-cyan-500/30",
  Parsing: "bg-blue-500/15 text-blue-400 border-blue-500/30",
  Processing: "bg-blue-500/15 text-blue-400 border-blue-500/30",
  Completed: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  Failed: "bg-red-500/15 text-red-400 border-red-500/30",
};

function StatusBadge({ status }: { status: UploadStatus }) {
  return (
    <Badge variant="outline" className={`border ${statusStyles[status]}`}>
      {status}
    </Badge>
  );
}

async function downloadUploadFile(row: { id: string; fileName: string; module: string; status: string }) {
  if (isLiveApi()) {
    const url = await uploadsApi.getUploadDownloadUrl(row.id);
    window.open(url, "_blank", "noopener,noreferrer");
    return;
  }
  const content = `Mock export for ${row.fileName}\nModule: ${row.module}\nStatus: ${row.status}`;
  downloadBlob(content, row.fileName, "text/plain");
}

export function DataUploadHistoryTable() {
  const { history, isLoading } = useDataUploadHistory();
  const { invalidateData } = useInvalidateUploadHistory();
  const { removeDataUpload, showToast } = useUpload();
  const [search, setSearch] = useState("");
  const [moduleFilter, setModuleFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  const filtered = useMemo(() => {
    return history.filter((row) => {
      const q = search.toLowerCase();
      const matchSearch =
        !q ||
        row.fileName.toLowerCase().includes(q) ||
        row.module.toLowerCase().includes(q) ||
        row.id.toLowerCase().includes(q);
      const matchModule = moduleFilter === "all" || row.module === moduleFilter;
      const matchStatus = statusFilter === "all" || row.status === statusFilter;
      return matchSearch && matchModule && matchStatus;
    });
  }, [history, search, moduleFilter, statusFilter]);

  const handleDelete = async (row: DataUploadRecord) => {
    if (isLiveApi()) {
      try {
        await uploadsApi.deleteUpload(row.id);
        await invalidateData();
        showToast("Upload deleted", "info");
      } catch {
        showToast("Failed to delete upload", "error");
      }
      return;
    }
    removeDataUpload(row.id);
    showToast("Upload deleted", "info");
  };

  return (
    <HistoryShell
      title="Upload History"
      search={search}
      onSearch={setSearch}
      moduleFilter={moduleFilter}
      onModuleFilter={setModuleFilter}
      statusFilter={statusFilter}
      onStatusFilter={setStatusFilter}
      isLoading={isLoading}
    >
      <Table>
        <TableHeader>
          <TableRow className="border-[#2D3748] hover:bg-transparent">
            {["Upload ID", "File Name", "Module", "File Type", "Size", "Uploaded By", "Upload Time", "Status", "Action"].map((h) => (
              <TableHead key={h} className="sticky top-0 bg-[#111827] text-slate-400">{h}</TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {filtered.map((row) => (
            <TableRow key={row.id} className="border-[#2D3748]/60">
              <TableCell className="font-mono text-xs text-white">{row.id}</TableCell>
              <TableCell className="text-sm text-slate-200">{row.fileName}</TableCell>
              <TableCell className="text-sm text-slate-300">{row.module}</TableCell>
              <TableCell>{row.fileType}</TableCell>
              <TableCell>{row.size}</TableCell>
              <TableCell>{row.uploadedBy}</TableCell>
              <TableCell className="text-xs text-slate-400">{formatUploadTime(row.uploadTime)}</TableCell>
              <TableCell><StatusBadge status={row.status} /></TableCell>
              <TableCell>
                <div className="flex gap-1">
                  <Button variant="ghost" size="icon" className="h-7 w-7 text-slate-400 hover:text-white" onClick={() => showToast(`Viewing ${row.fileName}`, "info")}><Eye className="h-3.5 w-3.5" /></Button>
                  <Button variant="ghost" size="icon" className="h-7 w-7 text-slate-400 hover:text-white" onClick={async () => {
                    try {
                      await downloadUploadFile(row);
                      showToast(`Download started: ${row.fileName}`, "success");
                    } catch {
                      showToast("Download failed", "error");
                    }
                  }}><Download className="h-3.5 w-3.5" /></Button>
                  {row.status === "Failed" && (
                    <Button variant="ghost" size="icon" className="h-7 w-7 text-[#7C3AED]" onClick={() => showToast(`Retry queued: ${row.fileName}`, "info")}><RefreshCw className="h-3.5 w-3.5" /></Button>
                  )}
                  <Button variant="ghost" size="icon" className="h-7 w-7 text-red-400" onClick={() => handleDelete(row)}><Trash2 className="h-3.5 w-3.5" /></Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </HistoryShell>
  );
}

export function LogUploadHistoryTable() {
  const { history, isLoading } = useLogUploadHistory();
  const { invalidateLog } = useInvalidateUploadHistory();
  const { removeLogUpload, showToast } = useUpload();
  const [search, setSearch] = useState("");
  const [moduleFilter, setModuleFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  const filtered = useMemo(() => {
    return history.filter((row) => {
      const q = search.toLowerCase();
      const matchSearch =
        !q ||
        row.fileName.toLowerCase().includes(q) ||
        row.module.toLowerCase().includes(q) ||
        row.lotId.toLowerCase().includes(q);
      const matchModule = moduleFilter === "all" || row.module === moduleFilter;
      const matchStatus = statusFilter === "all" || row.status === statusFilter;
      return matchSearch && matchModule && matchStatus;
    });
  }, [history, search, moduleFilter, statusFilter]);

  const handleDelete = async (row: LogUploadRecord) => {
    if (isLiveApi()) {
      try {
        await uploadsApi.deleteUpload(row.id);
        await invalidateLog();
        showToast("Upload deleted", "info");
      } catch {
        showToast("Failed to delete upload", "error");
      }
      return;
    }
    removeLogUpload(row.id);
    showToast("Upload deleted", "info");
  };

  return (
    <HistoryShell
      title="Upload History"
      search={search}
      onSearch={setSearch}
      moduleFilter={moduleFilter}
      onModuleFilter={setModuleFilter}
      statusFilter={statusFilter}
      onStatusFilter={setStatusFilter}
      isLoading={isLoading}
    >
      <Table>
        <TableHeader>
          <TableRow className="border-[#2D3748] hover:bg-transparent">
            {["Upload ID", "File Name", "Module", "Tester", "Lot ID", "Wafer ID", "Type", "Size", "Upload Time", "Status", "Processing", "By", "Action"].map((h) => (
              <TableHead key={h} className="sticky top-0 bg-[#111827] text-slate-400">{h}</TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {filtered.map((row) => (
            <TableRow key={row.id} className="border-[#2D3748]/60">
              <TableCell className="font-mono text-xs text-white">{row.id}</TableCell>
              <TableCell className="text-sm text-slate-200">{row.fileName}</TableCell>
              <TableCell>{row.module}</TableCell>
              <TableCell>{row.tester}</TableCell>
              <TableCell>{row.lotId}</TableCell>
              <TableCell>{row.waferId}</TableCell>
              <TableCell>{row.fileType}</TableCell>
              <TableCell>{row.size}</TableCell>
              <TableCell className="text-xs text-slate-400">{formatUploadTime(row.uploadTime)}</TableCell>
              <TableCell><StatusBadge status={row.status} /></TableCell>
              <TableCell>{row.processingTime}</TableCell>
              <TableCell>{row.uploadedBy}</TableCell>
              <TableCell>
                <div className="flex gap-1">
                  <Button variant="ghost" size="icon" className="h-7 w-7 text-slate-400 hover:text-white" onClick={() => showToast(`Viewing ${row.fileName}`, "info")}><Eye className="h-3.5 w-3.5" /></Button>
                  <Button variant="ghost" size="icon" className="h-7 w-7 text-slate-400 hover:text-white" onClick={async () => {
                    try {
                      await downloadUploadFile(row);
                      showToast(`Download started: ${row.fileName}`, "success");
                    } catch {
                      showToast("Download failed", "error");
                    }
                  }}><Download className="h-3.5 w-3.5" /></Button>
                  {row.status === "Failed" && (
                    <Button variant="ghost" size="icon" className="h-7 w-7 text-[#7C3AED]" onClick={() => showToast(`Retry queued: ${row.fileName}`, "info")}><RefreshCw className="h-3.5 w-3.5" /></Button>
                  )}
                  <Button variant="ghost" size="icon" className="h-7 w-7 text-red-400" onClick={() => handleDelete(row)}><Trash2 className="h-3.5 w-3.5" /></Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </HistoryShell>
  );
}

function HistoryShell({
  title,
  search,
  onSearch,
  moduleFilter,
  onModuleFilter,
  statusFilter,
  onStatusFilter,
  isLoading,
  children,
}: {
  title: string;
  search: string;
  onSearch: (v: string) => void;
  moduleFilter: string;
  onModuleFilter: (v: string) => void;
  statusFilter: string;
  onStatusFilter: (v: string) => void;
  isLoading?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="mt-6 rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/30">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#2D3748]/60 p-4">
        <h4 className="text-sm font-semibold text-white">{title}{isLoading ? " · Loading…" : ""}</h4>
        <div className="flex flex-wrap gap-2">
          <Input placeholder="Search uploads..." value={search} onChange={(e) => onSearch(e.target.value)} className="h-8 w-40 border-[#2D3748] bg-[#0A1020] text-xs" />
          <Select value={moduleFilter} onValueChange={(v) => onModuleFilter(v ?? "all")}>
            <SelectTrigger className="h-8 w-36 border-[#2D3748] bg-[#0A1020] text-xs"><SelectValue placeholder="Module" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Modules</SelectItem>
              <SelectItem value="Scan Chain Analysis">Scan Chain</SelectItem>
              <SelectItem value="Scan Chain">Scan Chain</SelectItem>
              <SelectItem value="MBIST Analysis">MBIST</SelectItem>
              <SelectItem value="MBIST">MBIST</SelectItem>
              <SelectItem value="LBIST Analysis">LBIST</SelectItem>
              <SelectItem value="Cost Intelligence">Cost</SelectItem>
            </SelectContent>
          </Select>
          <Select value={statusFilter} onValueChange={(v) => onStatusFilter(v ?? "all")}>
            <SelectTrigger className="h-8 w-32 border-[#2D3748] bg-[#0A1020] text-xs"><SelectValue placeholder="Status" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="Queued">Queued</SelectItem>
              <SelectItem value="Uploading">Uploading</SelectItem>
              <SelectItem value="Processing">Processing</SelectItem>
              <SelectItem value="Parsing">Parsing</SelectItem>
              <SelectItem value="Completed">Completed</SelectItem>
              <SelectItem value="Failed">Failed</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      <div className="max-h-[280px] overflow-auto">{children}</div>
    </div>
  );
}

export type { DataUploadRecord, LogUploadRecord };
