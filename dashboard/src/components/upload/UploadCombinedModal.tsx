"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { FileIcon, FileText, ShieldCheck, X } from "lucide-react";
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
import { UploadDropzone } from "@/components/upload/UploadDropzone";
import { buildProgressState, UploadProgressPanel } from "@/components/upload/UploadProgressPanel";
import { formatFileSize, formatNow, getFileExtension } from "@/lib/uploadData";
import { buildCombinedUploadZip } from "@/lib/api/combinedUploadZip";
import { performFileUpload, shouldUseLiveUploads } from "@/lib/api/uploadFlow";
import { useInvalidateUploadHistory } from "@/hooks/useUploadHistory";
import { useSessionUserName } from "@/stores/userStore";
import {
  DATA_FILE_EXTENSIONS,
  DATA_MAX_SIZE_GB,
  LOG_FILE_EXTENSIONS,
  LOG_MAX_SIZE_GB,
  type DataModule,
  type TesterType,
  type UploadProgressState,
} from "@/types/upload";

const stilAccept = {
  "application/octet-stream": [".stil", ".stdf", ".wgl", ".xml"],
  "application/xml": [".stil", ".wgl", ".xml", ".stdf"],
  "text/plain": [".stil", ".wgl"],
};

const logAccept = {
  "application/octet-stream": LOG_FILE_EXTENSIONS,
  "text/plain": [".log", ".txt"],
  "application/gzip": [".gz"],
  "application/zip": [".zip"],
  "application/json": [".json"],
  "application/xml": [".xml"],
  "text/csv": [".csv"],
};

interface UploadCombinedModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function UploadCombinedModal({ open, onOpenChange }: UploadCombinedModalProps) {
  const { showToast } = useUpload();
  const { invalidateData, invalidateLog } = useInvalidateUploadHistory();
  const sessionName = useSessionUserName();

  const [stilFile, setStilFile] = useState<File | null>(null);
  const [logFiles, setLogFiles] = useState<File[]>([]);
  const [module, setModule] = useState<DataModule>("Auto Detect");
  const [testerType, setTesterType] = useState<TesterType>("V93000");
  const [fab, setFab] = useState("Fab-12");
  const [tester, setTester] = useState("ATE-01");
  const [product, setProduct] = useState("Chip-X7");
  const [lotId, setLotId] = useState("lot-4421");
  const [waferId, setWaferId] = useState("wafer-12");
  const [deviceName, setDeviceName] = useState("Chip-X7");
  const [operator, setOperator] = useState(sessionName);
  const [notes, setNotes] = useState("");
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState<UploadProgressState | null>(null);
  const [detailsError, setDetailsError] = useState<string | null>(null);

  const detailsComplete =
    Boolean(module) &&
    Boolean(testerType) &&
    Boolean(fab.trim()) &&
    Boolean(tester.trim()) &&
    Boolean(product.trim()) &&
    Boolean(lotId.trim()) &&
    Boolean(waferId.trim()) &&
    Boolean(deviceName.trim()) &&
    Boolean(operator.trim());

  const canUpload = Boolean(stilFile) && logFiles.length > 0 && detailsComplete && !uploading;

  const reset = () => {
    setStilFile(null);
    setLogFiles([]);
    setProgress(null);
    setUploading(false);
    setDetailsError(null);
  };

  const handleStil = (selected: File[]) => {
    const file = selected[0];
    if (!file) return;
    const ext = getFileExtension(file.name);
    if (!DATA_FILE_EXTENSIONS.includes(ext) && ext !== ".stil") {
      showToast(`Unsupported data format: ${ext || "unknown"}`, "error");
      return;
    }
    setStilFile(file);
  };

  const handleLogs = (selected: File[]) => {
    const valid = selected.filter((f) => LOG_FILE_EXTENSIONS.includes(getFileExtension(f.name)));
    if (!valid.length) {
      showToast("No supported log files selected", "error");
      return;
    }
    setLogFiles((prev) => {
      const names = new Set(prev.map((f) => f.name.toLowerCase()));
      const next = [...prev];
      for (const f of valid) {
        if (!names.has(f.name.toLowerCase())) {
          next.push(f);
          names.add(f.name.toLowerCase());
        }
      }
      return next;
    });
  };

  const removeLog = (name: string) => {
    setLogFiles((prev) => prev.filter((f) => f.name !== name));
  };

  const handleUpload = async () => {
    if (!stilFile || !logFiles.length) return;
    if (!detailsComplete) {
      setDetailsError("Fill all required upload details before uploading.");
      showToast("Upload details are required", "error");
      return;
    }
    setDetailsError(null);
    setUploading(true);
    showToast("Packaging STIL + log files…", "info");

    const metadata = {
      fab: fab.trim(),
      tester: tester.trim(),
      product: product.trim(),
      lotId: lotId.trim(),
      waferId: waferId.trim(),
      deviceName: deviceName.trim(),
      operator: operator.trim(),
      notes: notes.trim(),
      testerType,
      stilFileName: stilFile.name,
      logFileNames: logFiles.map((f) => f.name).join(","),
      combinedUpload: "true",
    };

    try {
      const zipFile = await buildCombinedUploadZip(
        stilFile,
        logFiles,
        `${lotId.trim() || "lot"}_${waferId.trim() || "wafer"}_combined.zip`
      );
      const totalLabel = formatFileSize(
        stilFile.size + logFiles.reduce((s, f) => s + f.size, 0)
      );

      if (!shouldUseLiveUploads()) {
        showToast("Live API mode is required for combined STIL + log upload", "error");
        return;
      }

      showToast("Upload started", "info");
      const startedAt = Date.now();
      await performFileUpload(
        zipFile,
        module === "Auto Detect" ? "Scan Chain Analysis" : module,
        metadata,
        "data",
        (percent, stepLabel) =>
          setProgress(
            buildProgressState(
              percent,
              totalLabel,
              (Date.now() - startedAt) / 1000,
              stepLabel
            )
          )
      );
      await Promise.all([invalidateData(), invalidateLog()]);
      showToast("Combined upload completed — Pattern, Failure, and Scan Diagnosis will run on this dataset.", "success");
      reset();
      onOpenChange(false);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Upload failed";
      setProgress((prev) =>
        prev
          ? { ...prev, failed: true, errorMessage: message }
          : {
              percent: 0,
              speed: "0 MB/s",
              elapsed: "0s",
              remaining: "—",
              fileSize: formatFileSize(stilFile.size),
              failed: true,
              errorMessage: message,
            }
      );
      showToast(message, "error");
    } finally {
      setUploading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!uploading) { if (!v) reset(); onOpenChange(v); } }}>
      <DialogContent className="max-w-3xl" onClose={() => !uploading && onOpenChange(false)}>
        <DialogHeader>
          <DialogTitle>Upload STIL + ATE Logs</DialogTitle>
          <DialogDescription>
            Select one STIL (or data) file and one or more ATE log files. They are packaged into one upload and run through Parser → Pattern → Failure → Scan Diagnosis together.
          </DialogDescription>
        </DialogHeader>
        <DialogBody className="space-y-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <p className="text-xs font-medium text-slate-300">
                STIL / data file <span className="text-red-400">*</span>
              </p>
              <UploadDropzone
                accept={stilAccept}
                maxSizeBytes={DATA_MAX_SIZE_GB * 1024 ** 3}
                multiple={false}
                onFilesSelected={handleStil}
                label="Drop STIL / STDF / WGL"
                hint="Browse data file"
              />
              {stilFile && (
                <FileChip
                  name={stilFile.name}
                  size={formatFileSize(stilFile.size)}
                  icon="data"
                  onRemove={() => setStilFile(null)}
                />
              )}
            </div>
            <div className="space-y-2">
              <p className="text-xs font-medium text-slate-300">
                ATE log file(s) <span className="text-red-400">*</span>
              </p>
              <UploadDropzone
                accept={logAccept}
                maxSizeBytes={LOG_MAX_SIZE_GB * 1024 ** 3}
                multiple
                onFilesSelected={handleLogs}
                label="Drop one or more logs"
                hint="Browse log files"
              />
              {logFiles.length > 0 && (
                <div className="max-h-28 space-y-1.5 overflow-y-auto">
                  {logFiles.map((f) => (
                    <FileChip
                      key={f.name}
                      name={f.name}
                      size={formatFileSize(f.size)}
                      icon="log"
                      onRemove={() => removeLog(f.name)}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>

          {(stilFile || logFiles.length > 0) && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/40 p-3 text-xs text-slate-400"
            >
              Package: {stilFile ? "1 data file" : "no data file"} + {logFiles.length} log
              {logFiles.length === 1 ? "" : "s"}
              {stilFile ? ` · Ready ${formatNow()}` : ""}
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
            <Field label="Tester Type" required>
              <Select value={testerType} onValueChange={(v) => setTesterType((v ?? "V93000") as TesterType)}>
                <SelectTrigger className="border-[#2D3748] bg-[#0A1020]"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {["UltraFlex", "UltraFLEX Plus", "V93000", "J750", "T2000", "Other"].map((t) => (
                    <SelectItem key={t} value={t}>{t}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>
            <Field label="Fab" required>
              <Input value={fab} onChange={(e) => setFab(e.target.value)} className="border-[#2D3748] bg-[#0A1020]" />
            </Field>
            <Field label="Tester" required>
              <Input value={tester} onChange={(e) => setTester(e.target.value)} className="border-[#2D3748] bg-[#0A1020]" />
            </Field>
            <Field label="Product" required>
              <Input value={product} onChange={(e) => setProduct(e.target.value)} className="border-[#2D3748] bg-[#0A1020]" />
            </Field>
            <Field label="Lot ID" required>
              <Input value={lotId} onChange={(e) => setLotId(e.target.value)} placeholder="LOT-4821" className="border-[#2D3748] bg-[#0A1020]" />
            </Field>
            <Field label="Wafer ID" required>
              <Input value={waferId} onChange={(e) => setWaferId(e.target.value)} placeholder="W-12" className="border-[#2D3748] bg-[#0A1020]" />
            </Field>
            <Field label="Device Name" required>
              <Input value={deviceName} onChange={(e) => setDeviceName(e.target.value)} className="border-[#2D3748] bg-[#0A1020]" />
            </Field>
            <Field label="Operator" required>
              <Input value={operator} onChange={(e) => setOperator(e.target.value)} className="border-[#2D3748] bg-[#0A1020]" />
            </Field>
          </div>
          <Field label="Optional Notes">
            <Input value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Additional context..." className="border-[#2D3748] bg-[#0A1020]" />
          </Field>
          {detailsError && <p className="text-xs text-red-400">{detailsError}</p>}
          <div className="flex items-center gap-2 rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3 text-xs text-emerald-400">
            <ShieldCheck className="h-4 w-4 shrink-0" />
            One ZIP job · shared metadata · live Parser + all three agents
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" className="rounded-xl border-[#2D3748]" onClick={() => onOpenChange(false)} disabled={uploading}>
            Cancel
          </Button>
          <Button
            className="btn-glow rounded-xl bg-[#7C3AED] hover:bg-[#6D28D9]"
            onClick={handleUpload}
            disabled={!canUpload}
          >
            {uploading ? "Uploading…" : "Upload"}
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

function FileChip({
  name,
  size,
  icon,
  onRemove,
}: {
  name: string;
  size: string;
  icon: "data" | "log";
  onRemove: () => void;
}) {
  const Icon = icon === "log" ? FileText : FileIcon;
  return (
    <div className="flex items-center gap-2 rounded-lg border border-[#2D3748]/60 bg-[#0A1020]/60 px-2.5 py-1.5">
      <Icon className="h-3.5 w-3.5 shrink-0 text-[#7C3AED]" />
      <div className="min-w-0 flex-1">
        <p className="truncate text-xs font-medium text-white">{name}</p>
        <p className="text-[10px] text-slate-500">{size}</p>
      </div>
      <button
        type="button"
        onClick={onRemove}
        className="rounded p-0.5 text-slate-500 hover:bg-white/5 hover:text-white"
        aria-label={`Remove ${name}`}
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}
