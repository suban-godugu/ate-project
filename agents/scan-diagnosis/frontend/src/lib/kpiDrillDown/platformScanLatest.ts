import type { DiagnosisDashboard, KpiCard } from "@/lib/kpiDrillDown/diagnosisTypes";

type PlatformScanLatest = {
  job_id?: string;
  upload_id?: string;
  status?: string;
  metadata?: Record<string, unknown>;
  kpis?: {
    fail_count?: number;
    localized_flops?: number;
    affected_chains?: number;
    confidence?: number;
  };
  confidence?: number;
  recommendations?: Array<{ code?: string; severity?: string; message?: string }>;
  report?: {
    chain_diagnosis?: Record<string, number>;
    fail_flop_localization?: Record<string, number>;
    fail_types?: Record<string, number>;
    root_cause?: string;
    diagnosis_confidence?: number;
    inputs?: {
      pattern_kpis?: Record<string, number>;
      failure_kpis?: Record<string, number>;
    };
  };
};

function kpi(
  id: string,
  section: KpiCard["section"],
  label: string,
  value: string | number,
  caption?: string,
): KpiCard {
  return {
    id,
    section,
    label,
    value,
    caption: caption ?? null,
    status: "ok",
    badge: null,
    badge_tone: "neutral",
  };
}

/** Map VERILUMEN /scan/latest payload into the Scan Diagnosis dashboard shape. */
export function dashboardFromPlatformScan(latest: PlatformScanLatest): DiagnosisDashboard {
  const kpis = latest.kpis || {};
  const report = latest.report || {};
  const pattern = report.inputs?.pattern_kpis || {};
  const failure = report.inputs?.failure_kpis || {};
  const failCount = Number(kpis.fail_count ?? failure.fail_count ?? 0);
  const chains = Number(pattern.chain_count ?? kpis.affected_chains ?? 0);
  const flops = Number(kpis.localized_flops ?? 0);
  const confidence = Number(
    ((kpis.confidence ?? report.diagnosis_confidence ?? latest.confidence ?? 0) as number) * 100,
  );
  const fileName = String(latest.metadata?.file_name || "upload");
  const chainEntries = Object.entries(report.chain_diagnosis || {});
  const flopEntries = Object.entries(report.fail_flop_localization || {});

  return {
    title: "Scan Diagnosis",
    subtitle: latest.job_id || latest.upload_id || "",
    data_source: "fastapi-exports",
    mode: "live",
    filters: { lots: [], wafers: [], testers: [], fabs: [], dates: [] },
    dataset_summary: {
      stil_file: fileName,
      log_files: [fileName],
      log_file_count: 1,
      total_failure_records: failCount,
      failing_chains: chainEntries.length || Number(kpis.affected_chains || 0),
      all_chains: chains,
      failing_flops: flopEntries.length || flops,
    },
    ml_status: {
      active: true,
      failure_records_analyzed: failCount,
      root_cause_model: "scan-run",
      anomaly_model: "scan-run",
      confidence_model: "scan-run",
      root_causes_estimated: report.root_cause && report.root_cause !== "unknown" ? 1 : 0,
      anomaly_flagged_count: failCount,
      anomaly_flagged_pct: failCount ? 100 : 0,
      client_summary: `Root cause ${report.root_cause || "unknown"}`,
    },
    production_validation: {
      status: "ok",
      message: "Scan diagnosis results loaded",
    },
    kpis: [
      kpi("source_stil", "overview", "SOURCE — STIL", fileName, "Uploaded STIL"),
      kpi("source_logs", "overview", "SOURCE — LOGS", "1", "Uploaded logs"),
      kpi("total_failure_records", "overview", "TOTAL FAILURE RECORDS", failCount, "FAIL rows"),
      kpi("failing_chains", "overview", "FAILING CHAINS", chainEntries.length || Number(kpis.affected_chains || 0)),
      kpi("all_chains", "overview", "ALL CHAINS", chains),
      kpi("failing_flops", "overview", "FAILING FLOPS", flopEntries.length || flops),
      kpi("diagnosis_confidence", "ai", "DIAGNOSIS CONFIDENCE", `${confidence.toFixed(1)}%`),
      kpi("root_cause", "ai", "ROOT CAUSE", report.root_cause || "unknown"),
    ],
    ranking: chainEntries
      .sort((a, b) => b[1] - a[1])
      .slice(0, 20)
      .map(([chain, failure_count]) => ({ chain, failure_count })),
    correlations: [],
    shift_capture: {},
    confidence: {
      diagnosis_confidence: confidence / 100,
      root_cause: report.root_cause || "unknown",
    },
    topology_summary: {},
    breaks_table: [],
    cells_table: flopEntries.map(([cell, count]) => ({ cell, count })),
    reports_meta: {
      recommendations: latest.recommendations || [],
      job_id: latest.job_id || latest.upload_id,
    },
    footer: latest.job_id || latest.upload_id || "—",
  };
}

export async function fetchPlatformScanLatest(): Promise<PlatformScanLatest | null> {
  try {
    // Prefix keeps the request on this agent when proxied under /embed/scan.
    const apiBase = (process.env.NEXT_PUBLIC_API_BASE ?? "").replace(/\/$/, "");
    const res = await fetch(`${apiBase}/api/v1/scan/latest`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as PlatformScanLatest;
  } catch {
    return null;
  }
}
