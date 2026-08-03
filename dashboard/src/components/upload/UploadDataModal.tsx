"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { CheckCircle2, FileIcon, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogBody,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useUpload } from "@/contexts/UploadContext";
import { DataUploadHistoryTable } from "@/components/upload/UploadHistoryTable";
import { UploadDropzone } from "@/components/upload/UploadDropzone";
import { buildProgressState, simulateUpload, UploadProgressPanel } from "@/components/upload/UploadProgressPanel";
import { formatFileSize, formatNow, getFileExtension } from "@/lib/uploadData";
import { performFileUpload, shouldUseLiveUploads } from "@/lib/api/uploadFlow";
import { useInvalidateUploadHistory } from "@/hooks/useUploadHistory";
import { useSessionUserName } from "@/stores/userStore";
import { DATA_FILE_EXTENSIONS, DATA_MAX_SIZE_GB, type DataModule, type UploadProgressState } from "@/types/upload";

const acceptMap = {
  "application/octet-stream": DATA_FILE_EXTENSIONS,
  "text/csv": [".csv"],
  "application/json": [".json"],
  "application/zip": [".zip"],
  "application/xml": [".xml", ".stdf", ".stil", ".wgl"],
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
};

interface UploadDataModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function UploadDataModal({ open, onOpenChange }: UploadDataModalProps) {
  const { addDataUpload, updateDataStatus, showToast } = useUpload();
  const { invalidateData } = useInvalidateUploadHistory();
  const uploadedBy = useSessionUserName();
  const [files, setFiles] = useState<File[]>([]);
  const [module, setModule] = useState<DataModule>("Auto Detect");
  const [fab, setFab] = useState("Fab-12");
  const [tester, setTester] = useState("ATE-01");
  const [product, setProduct] = useState("Chip-X7");
  const [lotId, setLotId] = useState("");
  const [waferId, setWaferId] = useState("");
  const [notes, setNotes] = useState("");
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState<UploadProgressState | null>(null);
  const [fileInfo, setFileInfo] = useState<{ name: string; size: string; time: string } | null>(null);
  const [detailsError, setDetailsError] = useState<string | null>(null);

  const reset = () => {
    setFiles([]);
    setProgress(null);
    setFileInfo(null);
    setUploading(false);
    setDetailsError(null);
  };

  const detailsComplete =
    Boolean(fab.trim()) &&
    Boolean(tester.trim()) &&
    Boolean(product.trim()) &&
    Boolean(lotId.trim()) &&
    Boolean(waferId.trim()) &&
    Boolean(module);

  const handleFiles = (selected: File[]) => {
    setFiles(selected);
    if (selected[0]) {
      setFileInfo({ name: selected[0].name, size: formatFileSize(selected[0].size), time: formatNow() });
    }
  };

  const handleUpload = async () => {
    if (!files.length) return;
    if (!detailsComplete) {
      setDetailsError("Fill all required upload details (Fab, Tester, Product, Lot ID, Wafer ID) before uploading.");
      showToast("Upload details are required", "error");
      return;
    }
    setDetailsError(null);
    const file = files[0];
    const ext = getFileExtension(file.name).replace(".", "").toUpperCase() || "FILE";
    setUploading(true);
    showToast("Upload started", "info");

    const metadata = {
      fab: fab.trim(),
      tester: tester.trim(),
      product: product.trim(),
      lotId: lotId.trim(),
      waferId: waferId.trim(),
      notes: notes.trim(),
    };

    if (shouldUseLiveUploads()) {
      try {
        const startedAt = Date.now();
        await performFileUpload(
          file,
          module === "Auto Detect" ? "Scan Chain Analysis" : module,
          metadata,
          "data",
          (percent, stepLabel) =>
            setProgress(
              buildProgressState(
                percent,
                formatFileSize(file.size),
                (Date.now() - startedAt) / 1000,
                stepLabel
              )
            )
        );
        await invalidateData();
        showToast("File uploaded successfully. Dashboards will refresh with new data.", "success");
        reset();
        onOpenChange(false);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Upload failed";
        await invalidateData();
        setProgress((prev) =>
          prev
            ? {
                ...prev,
                failed: true,
                errorMessage: message,
                failedStage: message.includes("Failed at")
                  ? message.split(":")[0]?.replace("Failed at ", "")
                  : undefined,
              }
            : {
                percent: 0,
                speed: "0 MB/s",
                elapsed: "0s",
                remaining: "—",
                fileSize: formatFileSize(file.size),
                failed: true,
                errorMessage: message,
              }
        );
        showToast(message, "error");
      } finally {
        setUploading(false);
      }
      return;
    }

    const id = addDataUpload({
      fileName: file.name,
      module: module === "Auto Detect" ? "Scan Chain Analysis" : module,
      fileType: ext,
      size: formatFileSize(file.size),
      uploadedBy,
      status: "Uploading",
    });
    updateDataStatus(id, "Uploading");
    await simulateUpload((percent, elapsed) => {
      setProgress(buildProgressState(percent, formatFileSize(file.size), elapsed));
    });
    updateDataStatus(id, "Processing");
    await new Promise((r) => setTimeout(r, 800));
    updateDataStatus(id, "Completed");
    setUploading(false);
    showToast("File uploaded successfully. Dashboards will refresh with new data.", "success");
    showToast("AI analysis ready for imported dataset.", "info");
    reset();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!uploading) { if (!v) reset(); onOpenChange(v); } }}>
      <DialogContent className="max-w-3xl" onClose={() => !uploading && onOpenChange(false)}>
        <DialogHeader>
          <DialogTitle>Upload Test Data</DialogTitle>
          <DialogDescription>
            Import ATE files for Scan Chain, MBIST, LBIST, Wafer Analysis, and Cost Intelligence. Files upload directly to MinIO when live API mode is enabled.
          </DialogDescription>
        </DialogHeader>
        <DialogBody className="space-y-5">
          <UploadDropzone
            accept={acceptMap}
            maxSizeBytes={DATA_MAX_SIZE_GB * 1024 ** 3}
            multiple
            onFilesSelected={handleFiles}
            label="Drag & Drop files here"
            hint="Click to Browse"
          />
          <div className="rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/40 p-4">
            <p className="mb-2 text-xs font-medium text-slate-400">Supported formats</p>
            <p className="text-xs text-slate-500">STDF (.stdf) · STIL (.stil) · WGL (.wgl) · CSV · Excel (.xlsx) · JSON · ZIP · XML — Max {DATA_MAX_SIZE_GB} GB</p>
          </div>
          {fileInfo && (
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="grid gap-3 rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/40 p-4 sm:grid-cols-3">
              <InfoItem label="File Name" value={fileInfo.name} />
              <InfoItem label="File Size" value={fileInfo.size} />
              <InfoItem label="Upload Time" value={fileInfo.time} />
            </motion.div>
          )}
          {progress && <UploadProgressPanel progress={progress} uploading={uploading} />}
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Dataset Category" required>
              <Select value={module} onValueChange={(v) => setModule((v ?? "Auto Detect") as DataModule)}>
                <SelectTrigger className="border-[#2D3748] bg-[#0A1020]"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {["Auto Detect", "Scan Chain Analysis", "MBIST Analysis", "LBIST Analysis", "Cost Intelligence", "Recommendation Analysis"].map((m) => (
                    <SelectItem key={m} value={m}>{m}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>
            <Field label="Fab" required><Input value={fab} onChange={(e) => setFab(e.target.value)} className="border-[#2D3748] bg-[#0A1020]" /></Field>
            <Field label="Tester" required><Input value={tester} onChange={(e) => setTester(e.target.value)} className="border-[#2D3748] bg-[#0A1020]" /></Field>
            <Field label="Product" required><Input value={product} onChange={(e) => setProduct(e.target.value)} className="border-[#2D3748] bg-[#0A1020]" /></Field>
            <Field label="Lot ID" required><Input value={lotId} onChange={(e) => setLotId(e.target.value)} placeholder="LOT-4821" className="border-[#2D3748] bg-[#0A1020]" /></Field>
            <Field label="Wafer ID" required><Input value={waferId} onChange={(e) => setWaferId(e.target.value)} placeholder="W-12" className="border-[#2D3748] bg-[#0A1020]" /></Field>
          </div>
          <Field label="Optional Notes">
            <Input value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Additional context..." className="border-[#2D3748] bg-[#0A1020]" />
          </Field>
          {detailsError && <p className="text-xs text-red-400">{detailsError}</p>}
          <div className="flex items-center gap-2 rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3 text-xs text-emerald-400">
            <ShieldCheck className="h-4 w-4 shrink-0" />
            Extension validated · Checksum verified · {shouldUseLiveUploads() ? "Live upload pipeline" : "Mock simulation mode"}
          </div>
          <DataUploadHistoryTable />
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" className="rounded-xl border-[#2D3748]" onClick={() => onOpenChange(false)} disabled={uploading}>Cancel</Button>
          <Button className="btn-glow rounded-xl bg-[#7C3AED] hover:bg-[#6D28D9]" onClick={handleUpload} disabled={!files.length || !detailsComplete || uploading}>
            {uploading ? "Uploading..." : "Upload"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function Field({ label, children, required }: { label: string; children: React.ReactNode; required?: boolean }) {
  return (
    <div>
      <Label className="mb-1.5 text-xs text-slate-400">
        {label}
        {required ? <span className="ml-0.5 text-red-400">*</span> : null}
      </Label>
      {children}
    </div>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start gap-2">
      <FileIcon className="mt-0.5 h-4 w-4 text-[#7C3AED]" />
      <div>
        <p className="text-[10px] uppercase tracking-wider text-slate-500">{label}</p>
        <p className="text-sm font-medium text-white">{value}</p>
      </div>
    </div>
  );
}

export function UploadSuccessBanner({ visible }: { visible: boolean }) {
  if (!visible) return null;
  return (
    <div className="flex items-center gap-2 text-sm text-emerald-400">
      <CheckCircle2 className="h-4 w-4" />
      File uploaded successfully.
    </div>
  );
}
