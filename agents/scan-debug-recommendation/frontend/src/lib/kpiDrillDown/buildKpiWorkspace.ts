import { KPI_VIS_MAP, MOCK_KPIS, SECTION_PROFILES } from "@/lib/recommendationData";
import type { KpiWorkspace, ScanDebugKpiId } from "@/types/kpiDrillDown";

function titleFor(kpiId: ScanDebugKpiId) {
  return MOCK_KPIS.find((k) => k.id === kpiId)?.title ?? kpiId;
}

function sectionTitle(kpiId: ScanDebugKpiId) {
  const section = MOCK_KPIS.find((k) => k.id === kpiId)?.section;
  return SECTION_PROFILES.find((s) => s.id === section)?.title ?? "Scan Debug";
}

export function buildKpiWorkspace(kpiId: ScanDebugKpiId): KpiWorkspace {
  const kpi = MOCK_KPIS.find((k) => k.id === kpiId);
  const title = titleFor(kpiId);

  const decision = {
    executiveSummary: `${title} is ${String(kpi?.status ?? "at_risk").replace("_", " ")} versus target ${kpi?.target}. Section: ${sectionTitle(kpiId)}.`,
    rootCause:
      kpiId.includes("timing") || kpiId === "worst_slack"
        ? "Capture clock path slack violation with correlated scan mismatch density."
        : kpiId.includes("power") || kpiId === "peak_switching"
          ? "Elevated IR-drop during capture with peak switching above design envelope."
          : kpiId.includes("defect")
            ? "Bitmap cluster consistent with physical defect localization."
            : kpiId.includes("constraint") || kpiId === "coverage_impact" || kpiId === "pending_review"
              ? "ATPG constraint / mask mismatch reducing effective coverage."
              : "Scan chain continuity break with shifter signature failure.",
    confidence: typeof kpi?.value === "string" && kpi.value.includes("%")
      ? Number(String(kpi.value).replace("%", "")) / 100
      : 0.84,
    businessImpact: "Projected +0.9% to +2.4% yield recovery and 2–8% ATE runtime reduction if applied.",
    risk: kpi?.severity === "critical" ? "High — production lots blocked" : "Medium — controlled rollout recommended",
    recommendation:
      "Approve primary AI action, assign owning engineer, and generate ATPG/pattern update package.",
    whatFailed: `${title} breached engineering target (${kpi?.value} vs ${kpi?.target}).`,
    whyAiRecommended:
      "DQN policy scored this action highest from 10-D state (mismatch, shifter, chains, timing/power flags, bitmap density).",
    whatImproves: "Yield recovery, lower debug cycle time, restored coverage, and reduced false-fail volume.",
    shouldApprove:
      (kpi?.severity === "critical" || kpi?.severity === "high") && (kpi?.trendPct ?? 0) >= 0
        ? "Yes — approve with regression gate."
        : "Review with timing/power stakeholders before approve.",
  };

  return {
    kpiId,
    title,
    decision,
    summaryCards: [
      { label: "Current", value: String(kpi?.value ?? "—") },
      { label: "Target", value: String(kpi?.target ?? "—") },
      { label: "Affected Chains", value: "SC_0142, SC_0087, SC_0211" },
      { label: "Affected Patterns", value: "126" },
      { label: "Lots", value: "9" },
      { label: "Wafers", value: "47" },
      { label: "Coverage", value: "98.2%" },
      { label: "Power", value: "1.14× baseline" },
      { label: "Runtime", value: "4.6h / lot" },
      { label: "Cost", value: "$184K / qtr" },
      { label: "Yield", value: "+1.6% opp." },
      { label: "Business Impact", value: "High" },
    ],
    visualizationType: KPI_VIS_MAP[kpiId],
    vizSeries: [
      { label: "SC_0142", value: 94 },
      { label: "SC_0087", value: 81 },
      { label: "SC_0211", value: 76 },
      { label: "SC_0199", value: 71 },
      { label: "SC_0033", value: 58 },
      { label: "SC_0056", value: 44 },
    ],
    breakdown: [
      { dimension: "Tester", value: "ATE-07", share: 28 },
      { dimension: "Lot", value: "LOT_1", share: 22 },
      { dimension: "Wafer", value: "W12", share: 18 },
      { dimension: "Pattern", value: "PAT_SCAN_A", share: 15 },
      { dimension: "Scan Chain", value: "SC_0142", share: 14 },
      { dimension: "Clock Domain", value: "CLK_CAP", share: 12 },
      { dimension: "Power Domain", value: "PD_CORE", share: 10 },
      { dimension: "Fault Model", value: "Stuck-at", share: 35 },
      { dimension: "Module", value: "DFT_TOP", share: 20 },
    ],
    impact: [
      { label: "Coverage", before: "96.4%", after: "98.2%", delta: "+1.8pp" },
      { label: "Yield", before: "91.1%", after: "92.7%", delta: "+1.6pp" },
      { label: "Runtime", before: "5.1h", after: "4.6h", delta: "-9.8%" },
      { label: "Power", before: "1.42×", after: "1.14×", delta: "-19.7%" },
      { label: "Pattern Reduction", before: "0", after: "12%", delta: "-12%" },
      { label: "Cost Saving", before: "$0", after: "$184K", delta: "+$184K" },
      { label: "Memory Usage", before: "18.2GB", after: "16.4GB", delta: "-9.9%" },
    ],
    timeline: [
      { id: "gen", label: "Generated", at: "2026-07-14 09:12", status: "done" },
      { id: "rev", label: "Reviewed", at: "2026-07-15 11:40", status: "done" },
      { id: "apr", label: "Approved", at: "—", status: "active" },
      { id: "upd", label: "Pattern Updated", at: "—", status: "upcoming" },
      { id: "val", label: "Validation", at: "—", status: "upcoming" },
      { id: "reg", label: "Regression", at: "—", status: "upcoming" },
      { id: "prd", label: "Production", at: "—", status: "upcoming" },
    ],
    rawRows: [
      {
        pattern: "PAT_SCAN_A",
        chain: "SC_0142",
        vector: "V00481",
        cell: "U184",
        clock: "CLK_CAP",
        coverage: 97.1,
        fault: "SA0",
        runtimeMs: 412,
        powerMw: 186,
        confidence: 0.94,
        recommendationScore: 0.91,
      },
      {
        pattern: "PAT_SCAN_B",
        chain: "SC_0087",
        vector: "V00112",
        cell: "U092",
        clock: "CLK_LAUNCH",
        coverage: 95.4,
        fault: "TR",
        runtimeMs: 388,
        powerMw: 204,
        confidence: 0.88,
        recommendationScore: 0.84,
      },
      {
        pattern: "PAT_ATPG_C",
        chain: "SC_0211",
        vector: "V00901",
        cell: "U301",
        clock: "CLK_CAP",
        coverage: 96.0,
        fault: "SA1",
        runtimeMs: 455,
        powerMw: 241,
        confidence: 0.81,
        recommendationScore: 0.79,
      },
    ],
    copilotStarters: [
      "Why was this recommendation generated?",
      "Explain root cause.",
      "Compare similar failures.",
      "Estimate yield improvement.",
      "Estimate runtime reduction.",
      "Suggest alternative repair.",
      "Show historical success.",
      "Compare lots.",
      "Compare wafers.",
    ],
    howToImplement:
      kpiId === "broken_chains"
        ? "Run shift-only patterns from failing bitmap; find first bit position where expected≠observed consistently across patterns → maps to chain # + cell index via STIL chain order"
        : null,
    diagnosisResults:
      kpiId === "broken_chains"
        ? [
            {
              result: "Chain 1, break isolated at bit position 72 (cell SDFF_72)",
              chain: "Chain 1",
              candidateBit: 72,
              cellLabel: "SDFF_72",
              scanLength: 234,
            },
            {
              result: "Chain 14, break isolated at bit position 90 (cell SDFF_90)",
              chain: "Chain 14",
              candidateBit: 90,
              cellLabel: "SDFF_90",
              scanLength: 234,
            },
            {
              result: "Chain 5, break isolated at bit position 106 (cell SDFF_106)",
              chain: "Chain 5",
              candidateBit: 106,
              cellLabel: "SDFF_106",
              scanLength: 234,
            },
          ]
        : [],
    layout: kpiId === "broken_chains" ? "broken_chains_clean" : "default",
  };
}
