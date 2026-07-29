"use client";

import type { DecisionPanelData } from "@/types/kpiDrillDown";

export function KpiScanDebugDecisionPanel({
  decision,
  onAction,
}: {
  decision: DecisionPanelData;
  onAction: (action: string) => void;
}) {
  return (
    <div className="flex h-full flex-col gap-4 overflow-y-auto p-4">
      <div>
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">AI Decision Panel</div>
        <h3 className="font-display text-lg font-semibold text-white">Executive Summary</h3>
        <p className="mt-2 text-sm text-slate-300">{decision.executiveSummary}</p>
      </div>

      <div className="grid grid-cols-1 gap-3">
        {[
          ["Root Cause", decision.rootCause],
          ["Business Impact", decision.businessImpact],
          ["Risk", decision.risk],
          ["Recommendation", decision.recommendation],
        ].map(([label, value]) => (
          <div key={label} className="rounded-xl border border-border/70 bg-white/5 p-3">
            <div className="text-[11px] uppercase tracking-wide text-slate-400">{label}</div>
            <div className="mt-1 text-sm text-slate-200">{value}</div>
          </div>
        ))}
        <div className="rounded-xl border border-primary/30 bg-primary/10 p-3">
          <div className="text-[11px] uppercase tracking-wide text-primary">Confidence</div>
          <div className="mt-1 font-display text-2xl font-semibold text-white">
            {Math.round(decision.confidence * 100)}%
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-border/70 bg-card/60 p-3">
        <div className="mb-2 text-[11px] uppercase tracking-wide text-slate-400">
          Four Engineering Questions
        </div>
        <ol className="space-y-2 text-sm text-slate-300">
          <li>
            <span className="text-primary">1. What failed?</span> {decision.whatFailed}
          </li>
          <li>
            <span className="text-primary">2. Why did AI recommend this?</span>{" "}
            {decision.whyAiRecommended}
          </li>
          <li>
            <span className="text-primary">3. What improves if applied?</span> {decision.whatImproves}
          </li>
          <li>
            <span className="text-primary">4. Should this be approved?</span> {decision.shouldApprove}
          </li>
        </ol>
      </div>

      <div className="mt-auto flex flex-wrap gap-2">
        {["Approve", "Reject", "Modify", "Assign"].map((a) => (
          <button
            key={a}
            type="button"
            onClick={() => onAction(a)}
            className={`rounded-xl px-3 py-2 text-sm ${
              a === "Approve"
                ? "bg-success/20 text-success border border-success/40"
                : a === "Reject"
                  ? "bg-danger/20 text-danger border border-danger/40"
                  : "border border-border bg-white/5 text-slate-200"
            }`}
          >
            {a}
          </button>
        ))}
      </div>
    </div>
  );
}
