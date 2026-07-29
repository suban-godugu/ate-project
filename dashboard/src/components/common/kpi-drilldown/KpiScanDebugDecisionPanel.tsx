"use client";

import { KpiWidgetRenderer } from "@/components/common/kpi-drilldown/KpiWidgetRenderer";
import { KpiTopologyPanel } from "@/components/common/kpi-drilldown/KpiTopologyPanel";
import {
  KpiAiDecisionPanel,
  KpiApprovalCenterPanel,
} from "@/components/common/kpi-drilldown/KpiRecommendationPanels";
import type {
  KpiAiDecisionOverview,
  KpiAiExplanation,
  KpiApprovalAction,
  KpiTopologyEdge,
  KpiTopologyNode,
  KpiWidgetSpec,
} from "@/types/kpiDrillDown";

export function KpiScanDebugDecisionPanel({
  aiDecision,
  aiExplanation,
  approvalActions,
  heroWidget,
  showTopology,
  topologyGraph,
}: {
  aiDecision: KpiAiDecisionOverview;
  aiExplanation: KpiAiExplanation;
  approvalActions: KpiApprovalAction[];
  heroWidget?: KpiWidgetSpec;
  showTopology: boolean;
  topologyGraph: { nodes: KpiTopologyNode[]; edges: KpiTopologyEdge[] };
}) {
  const quickActions = approvalActions.slice(0, 3);

  return (
    <div className="grid gap-4 lg:grid-cols-5">
      <div className="space-y-4 lg:col-span-2">
        <KpiAiDecisionPanel data={aiDecision} variant="scanDebug" />
        <div className="rounded-xl border border-[rgba(139,92,246,0.25)] bg-[#121826]/80 p-4">
          <p className="text-[10px] font-bold uppercase tracking-wider text-[#64748B]">Root Cause & AI Explanation</p>
          <p className="mt-2 text-sm font-medium text-white">{aiExplanation.recommendationReason}</p>
          <div className="mt-4 space-y-2">
            {aiExplanation.featureImportance.slice(0, 3).map((f) => (
              <div key={f.feature}>
                <div className="mb-1 flex justify-between text-[11px]">
                  <span className="text-[#94A3B8]">{f.feature}</span>
                  <span className="text-[#C4B5FD]">{f.weight}%</span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-[#1e293b]">
                  <div className="h-full rounded-full bg-[#8B5CF6]" style={{ width: `${f.weight}%` }} />
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 grid gap-2 sm:grid-cols-2">
            <div className="rounded-lg border border-[#2D3748]/60 bg-[#0A1020]/60 px-3 py-2">
              <p className="text-[10px] uppercase tracking-wider text-[#64748B]">Confidence</p>
              <p className="text-sm font-bold text-emerald-400">{aiExplanation.confidence}%</p>
            </div>
            <div className="rounded-lg border border-[#2D3748]/60 bg-[#0A1020]/60 px-3 py-2">
              <p className="text-[10px] uppercase tracking-wider text-[#64748B]">Expected Outcome</p>
              <p className="text-xs text-[#CBD5E1]">{aiExplanation.expectedOutcome}</p>
            </div>
          </div>
        </div>
        <KpiApprovalCenterPanel actions={quickActions} />
      </div>
      <div className="min-h-[360px] lg:col-span-3">
        {showTopology ? (
          <div className="h-full min-h-[360px] rounded-2xl border border-[rgba(139,92,246,0.35)] bg-[#0A1020]/80 p-4">
            <p className="mb-3 text-[10px] font-bold uppercase tracking-wider text-[#8B5CF6]">
              Interactive Engineering Visualization
            </p>
            <KpiTopologyPanel
              nodes={topologyGraph.nodes}
              edges={topologyGraph.edges}
              highlightChainId="SC_14"
            />
          </div>
        ) : heroWidget ? (
          <div className="h-full min-h-[360px] rounded-2xl border border-[rgba(139,92,246,0.35)] bg-[#0A1020]/80 p-2">
            <p className="mb-2 px-2 pt-2 text-[10px] font-bold uppercase tracking-wider text-[#8B5CF6]">
              Interactive Engineering Visualization
            </p>
            <KpiWidgetRenderer
              widget={{
                ...heroWidget,
                span: 2,
                height: 340,
              }}
            />
          </div>
        ) : null}
      </div>
    </div>
  );
}
