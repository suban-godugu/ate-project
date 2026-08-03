"use client";

import { Loader2, RotateCcw } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import type { UploadProgressState } from "@/types/upload";
import { retryPipelineJob } from "@/lib/api/uploadFlow";

export function UploadProgressPanel({
  progress,
  uploading,
  onRetry,
}: {
  progress: UploadProgressState;
  uploading: boolean;
  onRetry?: () => void;
}) {
  return (
    <div className="rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/40 p-4">
      <div className="mb-3 flex items-center justify-between text-sm">
        <span className="font-medium text-white">
          {progress.failed ? "Pipeline Failed" : "Pipeline Progress"}
        </span>
        <span className="text-[#7C3AED]">{progress.percent}%</span>
      </div>
      <Progress value={progress.percent} />
      {progress.stageLabel && (
        <p className="mt-2 text-xs font-medium text-slate-200">{progress.stageLabel}</p>
      )}
      <div className="mt-3 grid gap-2 text-xs text-slate-400 sm:grid-cols-2 lg:grid-cols-4">
        <span>Speed: {progress.speed}</span>
        <span>Elapsed: {progress.elapsed}</span>
        <span>Remaining: {progress.remaining}</span>
        <span>Size: {progress.fileSize}</span>
      </div>
      {progress.failed && (
        <div className="mt-3 space-y-2 rounded-lg border border-red-500/30 bg-red-950/30 p-3 text-xs text-red-200">
          {progress.failedStage && <p>Failed stage: {progress.failedStage}</p>}
          {progress.errorMessage && <p>{progress.errorMessage}</p>}
          {(onRetry || progress.jobId) && (
            <Button
              type="button"
              size="sm"
              variant="outline"
              className="mt-1 h-8 gap-1 border-red-400/40 text-red-100"
              onClick={async () => {
                if (onRetry) {
                  onRetry();
                  return;
                }
                if (progress.jobId) {
                  await retryPipelineJob(progress.jobId);
                }
              }}
            >
              <RotateCcw className="h-3.5 w-3.5" />
              Retry
            </Button>
          )}
        </div>
      )}
      {uploading && !progress.failed && (
        <div className="mt-3 flex items-center gap-2 text-xs text-slate-400">
          <Loader2 className="h-3.5 w-3.5 animate-spin text-[#7C3AED]" />
          {progress.stageLabel || "Processing..."}
        </div>
      )}
    </div>
  );
}

export async function simulateUpload(
  onProgress: (percent: number, elapsedSec: number) => void
): Promise<void> {
  const steps = 20;
  for (let i = 1; i <= steps; i++) {
    await new Promise((r) => setTimeout(r, 120));
    onProgress(Math.round((i / steps) * 100), (i * 120) / 1000);
  }
}

export function buildProgressState(
  percent: number,
  fileSize: string,
  elapsedSec: number,
  stageLabel?: string
): UploadProgressState {
  const remainingSec =
    percent > 0 && percent < 100
      ? Math.max(0, Math.round((elapsedSec / percent) * (100 - percent)))
      : 0;
  const speed =
    elapsedSec > 0.5
      ? `${Math.max(0.1, percent / Math.max(elapsedSec, 1)).toFixed(1)} %/s`
      : "—";
  return {
    percent,
    speed,
    elapsed: `${Math.max(0, Math.round(elapsedSec))}s`,
    remaining: percent >= 100 ? "0s" : `${remainingSec}s`,
    fileSize,
    stageLabel,
  };
}
