"use client";

import { useCallback } from "react";
import { useActionStore } from "@/stores/actionStore";
import { useUploadStore } from "@/stores/uploadStore";
import { useNotifications } from "@/hooks/useNotifications";
import { isLiveApi } from "@/lib/api/config";
import { actionsApi } from "@/lib/api/actions";
import type { PrimaryActionResult } from "@/types/platform";

const actionResults: Record<string, Omit<PrimaryActionResult, "completedAt">> = {
  dashboard: {
    pageId: "dashboard",
    label: "AI Optimize",
    summary: "Optimization complete — projected savings identified across test patterns.",
    metrics: [
      { label: "Cost Reduction", value: "12.4%" },
      { label: "Time Savings", value: "8.2 min/wafer" },
      { label: "Projected Yield", value: "95.1%" },
      { label: "Total Savings", value: "$284K" },
    ],
  },
  "scan-chain": {
    pageId: "scan-chain",
    label: "Run AI Diagnosis",
    summary: "Scan chain diagnosis complete — root cause identified for critical chains.",
    metrics: [
      { label: "Critical Chains", value: "12" },
      { label: "Confidence", value: "91.2%" },
      { label: "Repair Success", value: "87%" },
    ],
  },
  mbist: {
    pageId: "mbist",
    label: "Run AI Diagnosis",
    summary: "MBIST diagnosis complete — memory repair candidates ranked.",
    metrics: [
      { label: "Repairable", value: "18" },
      { label: "Confidence", value: "88.6%" },
      { label: "Yield Impact", value: "+1.4%" },
    ],
  },
  lbist: {
    pageId: "lbist",
    label: "Run AI Diagnosis",
    summary: "LBIST diagnosis complete — logic block failures analyzed.",
    metrics: [
      { label: "Critical Blocks", value: "8" },
      { label: "Confidence", value: "90.1%" },
      { label: "Coverage Gap", value: "2.8%" },
    ],
  },
  "wafer-analysis": {
    pageId: "wafer-analysis",
    label: "Generate Yield Analysis",
    summary: "Yield analysis generated — defect hotspots and edge die losses identified.",
    metrics: [
      { label: "Yield", value: "93.8%" },
      { label: "Defect Hotspots", value: "4 zones" },
      { label: "Improvement", value: "+2.1%" },
    ],
  },
  wafervision: {
    pageId: "wafervision",
    label: "Analyze Wafer",
    summary: "WaferVision analysis complete — defect class, yield, and spatial clusters ready.",
    metrics: [
      { label: "Wafers", value: "Batch" },
      { label: "Spatial", value: "Clusters" },
      { label: "Zones", value: "6" },
    ],
  },
  "cost-intelligence": {
    pageId: "cost-intelligence",
    label: "Run Cost Optimization",
    summary: "Cost optimization complete — savings opportunities ranked by ROI.",
    metrics: [
      { label: "Savings", value: "$428K" },
      { label: "Cost Reduction", value: "14.2%" },
      { label: "Patterns Reduced", value: "24" },
    ],
  },
  "recommendation-analysis": {
    pageId: "recommendation-analysis",
    label: "Generate Recommendations",
    summary: "AI recommendations generated across all test modules.",
    metrics: [
      { label: "New Recommendations", value: "32" },
      { label: "Critical", value: "6" },
      { label: "Expected Yield Gain", value: "+3.2%" },
    ],
  },
  alerts: {
    pageId: "alerts",
    label: "Mark All Read",
    summary: "All visible alerts marked as read.",
    metrics: [{ label: "Alerts Cleared", value: "All" }],
  },
};

async function waitForJobResult(jobId: string): Promise<Record<string, unknown>> {
  return new Promise((resolve, reject) => {
    actionsApi.subscribeActionEvents(jobId, (event) => {
      if (event.status === "completed" && event.result) {
        resolve(event.result as Record<string, unknown>);
      }
      if (event.status === "failed") {
        reject(new Error("Job failed"));
      }
    }).catch(reject);
  });
}

export function usePrimaryAction(pageId: string) {
  const { runningAction, setRunningAction, setPrimaryResult } = useActionStore();
  const showToast = useUploadStore((s) => s.showToast);
  const { markAllRead } = useNotifications();
  const isRunning = runningAction === pageId;

  const run = useCallback(async () => {
    setRunningAction(pageId);
    try {
      if (pageId === "alerts") {
        markAllRead();
        showToast("All alerts marked as read", "success");
        return;
      }

      if (isLiveApi()) {
        const { job_id } = await actionsApi.triggerPrimaryAction(pageId);
        const result = await waitForJobResult(job_id);
        const primary: PrimaryActionResult = {
          pageId: String(result.pageId ?? pageId),
          label: String(result.label ?? "Action Complete"),
          summary: String(result.summary ?? ""),
          metrics: (result.metrics as PrimaryActionResult["metrics"]) ?? [],
          completedAt: String(result.completedAt ?? new Date().toLocaleString()),
        };
        setPrimaryResult(primary);
        showToast(`${primary.label} completed`, "success");
      } else {
        await new Promise((r) => setTimeout(r, 1800));
        const template = actionResults[pageId];
        if (template) {
          setPrimaryResult({
            ...template,
            completedAt: new Date().toLocaleString(),
          });
          showToast(`${template.label} completed`, "success");
        }
      }
    } finally {
      setRunningAction(null);
    }
  }, [pageId, setRunningAction, setPrimaryResult, showToast, markAllRead]);

  return { run, isRunning };
}

export function useAIDiagnosis(module: string) {
  const {
    aiDiagnosisRunning,
    aiDiagnosisStep,
    aiDiagnosisResult,
    setAIDiagnosisRunning,
    setAIDiagnosisStep,
    setAIDiagnosisResult,
  } = useActionStore();
  const showToast = useUploadStore((s) => s.showToast);

  const stepIndexFor = (step: string) => {
    const order = ["collect", "analyze", "insight", "complete"];
    const idx = order.indexOf(step);
    return idx >= 0 ? idx : 0;
  };

  const run = useCallback(async () => {
    setAIDiagnosisRunning(true);
    setAIDiagnosisResult(null);

    if (isLiveApi()) {
      try {
        const { job_id } = await actionsApi.triggerAIDiagnosis(module);
        await new Promise<void>((resolve, reject) => {
          actionsApi.subscribeActionEvents(job_id, (event) => {
            if (event.step) setAIDiagnosisStep(stepIndexFor(String(event.step)));
            if (event.status === "completed" && event.result) {
              const r = event.result as Record<string, unknown>;
              setAIDiagnosisResult({
                rootCause: String(r.rootCause ?? ""),
                confidence: Number(r.confidence ?? 0),
                recommendation: String(r.recommendation ?? ""),
                estimatedYieldImpact: String(r.estimatedYieldImpact ?? ""),
              });
              resolve();
            }
            if (event.status === "failed") reject(new Error("Diagnosis failed"));
          }).catch(reject);
        });
        showToast("AI diagnosis complete", "success");
      } catch {
        showToast("AI diagnosis failed", "error");
      } finally {
        setAIDiagnosisRunning(false);
      }
      return;
    }

    const steps = ["Collect Data", "Analyze", "Generate AI Insight", "Complete"];
    for (let i = 0; i < steps.length; i++) {
      setAIDiagnosisStep(i);
      await new Promise((r) => setTimeout(r, 700));
    }
    setAIDiagnosisResult({
      rootCause:
        module === "scan-chain"
          ? "Clock gating defect on SC-4821 — hold time violation at M4-M5"
          : module === "mbist"
            ? "SRAM Bank-2 coupling fault — repair candidate identified"
            : "LB-GPU MISR mismatch — transition fault in logic block",
      confidence: 88 + (module.length % 8),
      recommendation:
        "Retest affected patterns, apply compression optimization, and gate lot until verification completes.",
      estimatedYieldImpact: "+1.8%",
    });
    setAIDiagnosisRunning(false);
    showToast("AI diagnosis complete", "success");
  }, [module, setAIDiagnosisRunning, setAIDiagnosisStep, setAIDiagnosisResult, showToast]);

  return { run, isRunning: aiDiagnosisRunning, step: aiDiagnosisStep, result: aiDiagnosisResult };
}
