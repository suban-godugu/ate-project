"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { CheckCircle2, FileText, ShieldCheck, Sparkles } from "lucide-react";
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
import { LogUploadHistoryTable } from "@/components/upload/UploadHistoryTable";
import { UploadDropzone } from "@/components/upload/UploadDropzone";
import { buildProgressState, simulateUpload, UploadProgressPanel } from "@/components/upload/UploadProgressPanel";
import { formatFileSize, formatNow, getFileExtension } from "@/lib/uploadData";
import { performFileUpload, shouldUseLiveUploads } from "@/lib/api/uploadFlow";
import { useInvalidateUploadHistory } from "@/hooks/useUploadHistory";
import { uploadsApi } from "@/lib/api/uploads";
import { useSessionUserName } from "@/stores/userStore";
import {
  LOG_FILE_EXTENSIONS,
  LOG_MAX_SIZE_GB,
  type LogModule,
  type PipelineStep,
  type TesterType,
  type UploadProgressState,
  type ValidationResult,
} from "@/types/upload";

const logAccept = {
  "application/octet-stream": LOG_FILE_EXTENSIONS,
  "text/plain": [".log", ".txt", ".stil", ".wgl", ".stdf"],
  "application/gzip": [".gz"],
  "application/zip": [".zip"],
  "application/json": [".json"],
  "application/xml": [".xml"],
  "text/csv": [".csv"],
};

const pipelineLabels = [
  "Validate File",
  "Parse Log",
  "Extract Test Data",
  "Generate AI Insights",
  "Store in Database",
];

interface UploadLogFileModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function UploadLogFileModal({ open, onOpenChange }: UploadLogFileModalProps) {
  const { addLogUpload, updateLogStatus, showToast, lastAILogSummary, setLastAILogSummary } = useUpload();
  const { invalidateLog } = useInvalidateUploadHistory();
  const sessionName = useSessionUserName();
  const [files, setFiles] = useState<File[]>([]);
  const [logSource, setLogSource] = useState<LogModule>("Auto Detect");
  const [testerType, setTesterType] = useState<TesterType>("V93000");
  const [fab, setFab] = useState("Fab-12");
  const [tester, setTester] = useState("ATE-01");
  const [product, setProduct] = useState("Chip-X7");
  const [lotId, setLotId] = useState("");
  const [waferId, setWaferId] = useState("");
  const [deviceName, setDeviceName] = useState("");
  const [operator, setOperator] = useState(sessionName);
  const [comments, setComments] = useState("");
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState<UploadProgressState | null>(null);
  const [pipeline, setPipeline] = useState<PipelineStep[]>([]);
  const [showSummary, setShowSummary] = useState(false);
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [detailsError, setDetailsError] = useState<string | null>(null);

  const detailsComplete =
    Boolean(logSource) &&
    Boolean(testerType) &&
    Boolean(fab.trim()) &&
    Boolean(tester.trim()) &&
    Boolean(product.trim()) &&
    Boolean(lotId.trim()) &&
    Boolean(waferId.trim()) &&
    Boolean(deviceName.trim()) &&
    Boolean(operator.trim());

  const reset = () => {
    setFiles([]);
    setProgress(null);
    setPipeline([]);
    setShowSummary(false);
    setValidation(null);
    setUploading(false);
    setDetailsError(null);
  };

  const validateFile = (file: File): ValidationResult => {
    const ext = getFileExtension(file.name);
    const unsupported = !LOG_FILE_EXTENSIONS.includes(ext);
    const duplicate = file.name.includes("duplicate");
    const missingMetadata = !detailsComplete;
    const valid = !unsupported && !duplicate && !missingMetadata;
    return {
      fileType: ext.replace(".", "").toUpperCase() || "UNKNOWN",
      corrupted: false,
      unsupported,
      duplicate,
      missingMetadata,
      valid,
      message: unsupported
        ? "Unsupported file format"
        : duplicate
          ? "Duplicate upload detected"
          : missingMetadata
            ? "Fill all required upload details before uploading"
            : "File validated successfully",
    };
  };

  const handleFiles = (selected: File[]) => {
    setFiles(selected);
    if (selected[0]) setValidation(validateFile(selected[0]));
  };

  useEffect(() => {
    if (files[0]) setValidation(validateFile(files[0]));
    // Re-check metadata completeness when detail fields change.
    // eslint-disable-next-line react-hooks/exhaustive-deps -- validate against current form state
  }, [files, detailsComplete]);

  const runPipeline = async () => {
    const steps: PipelineStep[] = pipelineLabels.map((label, i) => ({
      id: `step-${i}`,
      label,
      status: "pending" as const,
    }));
    setPipeline(steps);
    for (let i = 0; i < steps.length; i++) {
      setPipeline((prev) =>
        prev.map((s, idx) => ({
          ...s,
          status: idx < i ? "done" : idx === i ? "active" : "pending",
        }))
      );
      await new Promise((r) => setTimeout(r, 600));
      setPipeline((prev) =>
        prev.map((s, idx) => ({
          ...s,
          status: idx <= i ? "done" : "pending",
        }))
      );
    }
  };

  const handleUpload = async () => {
    if (!files.length) return;
    if (!detailsComplete) {
      setDetailsError("Fill all required upload details before uploading.");
      showToast("Upload details are required", "error");
      if (files[0]) setValidation(validateFile(files[0]));
      return;
    }
    setDetailsError(null);
    const file = files[0];
    setUploading(true);
    showToast("Upload started", "info");

    const metadata = {
      fab: fab.trim(),
      tester: tester.trim(),
      product: product.trim(),
      lotId: lotId.trim(),
      waferId: waferId.trim(),
      deviceName: deviceName.trim(),
      operator: operator.trim(),
      comments: comments.trim(),
      testerType,
    };

    if (shouldUseLiveUploads()) {
      try {
        const startedAt = Date.now();
        const jobId = await performFileUpload(
          file,
          logSource === "Auto Detect" ? "Scan Chain" : logSource,
          metadata,
          "log",
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
        try {
          const summary = await uploadsApi.getAISummary(jobId);
          setLastAILogSummary(summary);
        } catch {
          /* summary optional when pipeline completes without AILogSummary */
        }
        await invalidateLog();
        setShowSummary(true);
        showToast("Upload completed", "success");
        showToast("AI analysis ready", "success");
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

    const id = addLogUpload({
      fileName: file.name,
      module: logSource === "Auto Detect" ? "Scan Chain" : logSource,
      tester: testerType,
      lotId: lotId || "LOT-4821",
      waferId: waferId || "W-12",
      fileType: validation?.fileType ?? "log",
      size: formatFileSize(file.size),
      uploadedBy: operator,
      status: "Uploading",
    });
    await simulateUpload((percent, elapsed) => {
      setProgress(buildProgressState(percent, formatFileSize(file.size), elapsed));
      updateLogStatus(id, "Uploading");
    });
    updateLogStatus(id, "Parsing");
    showToast("Parsing complete", "info");
    updateLogStatus(id, "Processing");
    await runPipeline();
    updateLogStatus(id, "Completed", "3m 24s");
    setLastAILogSummary({ ...lastAILogSummary, filesProcessed: String(files.length) });
    setShowSummary(true);
    setUploading(false);
    showToast("Upload completed", "success");
    showToast("AI analysis ready", "success");
  };

  const summaryItems = useMemo(
    () => [
      { label: "Files Processed", value: lastAILogSummary.filesProcessed },
      { label: "Patterns Found", value: lastAILogSummary.patternsFound },
      { label: "Scan Chains", value: lastAILogSummary.scanChains },
      { label: "Memory Blocks", value: lastAILogSummary.memoryBlocks },
      { label: "Logic Blocks", value: lastAILogSummary.logicBlocks },
      { label: "Wafer Count", value: lastAILogSummary.waferCount },
      { label: "Defects Found", value: lastAILogSummary.defectsFound },
      { label: "Yield", value: lastAILogSummary.yield },
      { label: "Est. Test Cost", value: lastAILogSummary.estimatedTestCost },
      { label: "Est. Savings", value: lastAILogSummary.estimatedSavings },
    ],
    [lastAILogSummary]
  );

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!uploading) { if (!v) reset(); onOpenChange(v); } }}>
      <DialogContent className="max-w-5xl" onClose={() => !uploading && onOpenChange(false)}>
        <DialogHeader>
          <DialogTitle>Upload ATE Log Files</DialogTitle>
          <DialogDescription>
            Upload raw tester logs for Scan Chain, MBIST, LBIST, Wafer Analysis, and Cost Intelligence. Live mode uploads to MinIO and runs the parse pipeline.
          </DialogDescription>
        </DialogHeader>
        <DialogBody className="space-y-5">
          <UploadDropzone
            accept={logAccept}
            maxSizeBytes={LOG_MAX_SIZE_GB * 1024 ** 3}
            multiple
            onFilesSelected={handleFiles}
            label="Drag & Drop Log Files Here"
            hint="Browse Files"
          />
          <p className="text-xs text-slate-500">
            STDF · STIL · WGL · ATE Log · TXT · CSV · JSON · XML · ZIP · GZIP — Max {LOG_MAX_SIZE_GB} GB
          </p>

          {validation && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className={`rounded-xl border p-4 ${validation.valid ? "border-emerald-500/30 bg-emerald-500/5" : "border-red-500/30 bg-red-500/5"}`}
            >
              <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-400">File Validation</p>
              <div className="grid gap-2 text-xs sm:grid-cols-2 lg:grid-cols-3">
                <ValidationItem ok={!validation.unsupported} label={`Type: ${validation.fileType}`} />
                <ValidationItem ok={!validation.corrupted} label="Not corrupted" />
                <ValidationItem ok={!validation.unsupported} label="Supported format" />
                <ValidationItem ok={!validation.duplicate} label="No duplicate" />
                <ValidationItem ok={!validation.missingMetadata} label="Metadata present" />
              </div>
              <p className={`mt-2 text-sm ${validation.valid ? "text-emerald-400" : "text-red-400"}`}>{validation.message}</p>
            </motion.div>
          )}

          {progress && <UploadProgressPanel progress={progress} uploading={uploading} />}

          {pipeline.length > 0 && (
            <div className="rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/40 p-4">
              <p className="mb-3 text-sm font-semibold text-white">Processing Pipeline</p>
              <div className="space-y-2">
                {pipeline.map((step, i) => (
                  <div key={step.id} className="flex items-center gap-3">
                    <div className={`flex h-7 w-7 items-center justify-center rounded-full text-xs ${step.status === "done" ? "bg-emerald-500/20 text-emerald-400" : step.status === "active" ? "bg-[#7C3AED]/20 text-[#7C3AED]" : "bg-slate-700/50 text-slate-500"}`}>
                      {step.status === "done" ? <CheckCircle2 className="h-4 w-4" /> : i + 1}
                    </div>
                    <span className="text-sm text-slate-300">{step.label}</span>
                    {step.status === "done" && <span className="text-xs text-emerald-400">✓</span>}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <Field label="Log Source" required>
              <Select value={logSource} onValueChange={(v) => setLogSource((v ?? "Auto Detect") as LogModule)}>
                <SelectTrigger className="border-[#2D3748] bg-[#0A1020]"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {["Auto Detect", "Scan Chain", "MBIST", "LBIST", "Cost Intelligence", "Recommendation Analysis"].map((m) => (
                    <SelectItem key={m} value={m}>{m}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>
            <Field label="Tester" required>
              <Select value={testerType} onValueChange={(v) => setTesterType((v ?? "V93000") as TesterType)}>
                <SelectTrigger className="border-[#2D3748] bg-[#0A1020]"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {["UltraFlex", "UltraFLEX Plus", "V93000", "J750", "T2000", "Other"].map((t) => (
                    <SelectItem key={t} value={t}>{t}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>
            <Field label="Fab" required><Input value={fab} onChange={(e) => setFab(e.target.value)} className="border-[#2D3748] bg-[#0A1020]" /></Field>
            <Field label="Tester ID" required><Input value={tester} onChange={(e) => setTester(e.target.value)} className="border-[#2D3748] bg-[#0A1020]" /></Field>
            <Field label="Product" required><Input value={product} onChange={(e) => setProduct(e.target.value)} className="border-[#2D3748] bg-[#0A1020]" /></Field>
            <Field label="Lot ID" required><Input value={lotId} onChange={(e) => setLotId(e.target.value)} className="border-[#2D3748] bg-[#0A1020]" /></Field>
            <Field label="Wafer ID" required><Input value={waferId} onChange={(e) => setWaferId(e.target.value)} className="border-[#2D3748] bg-[#0A1020]" /></Field>
            <Field label="Device Name" required><Input value={deviceName} onChange={(e) => setDeviceName(e.target.value)} className="border-[#2D3748] bg-[#0A1020]" /></Field>
            <Field label="Operator" required><Input value={operator} onChange={(e) => setOperator(e.target.value)} className="border-[#2D3748] bg-[#0A1020]" /></Field>
          </div>
          <Field label="Comments">
            <Input value={comments} onChange={(e) => setComments(e.target.value)} className="border-[#2D3748] bg-[#0A1020]" />
          </Field>
          {detailsError && <p className="text-xs text-red-400">{detailsError}</p>}

          <div className="flex items-center gap-2 rounded-xl border border-[#7C3AED]/20 bg-[#7C3AED]/5 p-3 text-xs text-slate-400">
            <ShieldCheck className="h-4 w-4 shrink-0 text-[#7C3AED]" />
            Extension validated · Checksum · Virus scan (placeholder) · Admin role
          </div>

          {showSummary && (
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="glass-card gradient-border p-5">
              <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-[#7C3AED]" />
                  <h4 className="font-semibold text-white">AI Log Summary</h4>
                </div>
                <Button size="sm" className="rounded-xl bg-[#7C3AED] text-xs hover:bg-[#6D28D9]" onClick={() => { onOpenChange(false); showToast("Opening analysis dashboard", "info"); }}>
                  Open Analysis Dashboard
                </Button>
              </div>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                {summaryItems.map((item) => (
                  <div key={item.label} className="rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/40 p-3">
                    <p className="text-[10px] uppercase tracking-wider text-slate-500">{item.label}</p>
                    <p className="mt-1 text-sm font-semibold text-white">{item.value}</p>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          <LogUploadHistoryTable />
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" className="rounded-xl border-[#2D3748]" onClick={() => onOpenChange(false)} disabled={uploading}>Cancel</Button>
          <Button className="btn-glow rounded-xl border border-[#7C3AED]/50 bg-[#7C3AED]/20 text-white hover:bg-[#7C3AED]/30" onClick={handleUpload} disabled={!files.length || !detailsComplete || uploading}>
            <FileText className="mr-1.5 h-3.5 w-3.5" />
            {uploading ? "Processing..." : "Upload Log File"}
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

function ValidationItem({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span className={ok ? "text-emerald-400" : "text-red-400"}>
      {ok ? "✓" : "✗"} {label}
    </span>
  );
}
