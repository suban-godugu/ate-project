"use client";

import { memo } from "react";
import type { AnalysisMetrics } from "@/stores/analysisStore";

type Props = {
  datasetName?: string;
  datasetDetail?: Record<string, unknown> | null;
  uploadDetail?: Record<string, unknown> | null;
  metrics?: AnalysisMetrics | null;
  fileCount?: number;
};

export const DatasetDetailsPanel = memo(function DatasetDetailsPanel({
  datasetName,
  datasetDetail,
  uploadDetail,
  metrics,
  fileCount,
}: Props) {
  const dataset = (datasetDetail as { dataset?: Record<string, unknown> })?.dataset || datasetDetail;
  const upload = (uploadDetail as { upload?: Record<string, unknown> })?.upload || uploadDetail;
  const uploads = (datasetDetail as { uploads?: Array<Record<string, unknown>> })?.uploads || [];

  if (!dataset && !upload && !metrics) {
    return (
      <div className="glass-panel rounded-2xl p-6 text-sm text-[var(--muted)]" data-testid="dataset-details">
        Dataset metadata appears after ingestion completes.
      </div>
    );
  }

  return (
    <div className="glass-panel rounded-2xl p-4" data-testid="dataset-details">
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
        Dataset Details
      </h3>
      <dl className="grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-3">
        <div>
          <dt className="text-[var(--muted)]">Dataset Name</dt>
          <dd className="font-medium">{String(dataset?.name || datasetName || "—")}</dd>
        </div>
        <div>
          <dt className="text-[var(--muted)]">Uploaded Files</dt>
          <dd>{fileCount ?? metrics?.imported_test_files ?? uploads.length ?? "—"}</dd>
        </div>
        <div>
          <dt className="text-[var(--muted)]">STIL Version</dt>
          <dd>{String(upload?.parser_id || (upload?.validation_report as { stil_version?: string } | undefined)?.stil_version || "—")}</dd>
        </div>
        <div>
          <dt className="text-[var(--muted)]">Tester Type</dt>
          <dd>{String(upload?.parser_id || "—")}</dd>
        </div>
        <div>
          <dt className="text-[var(--muted)]">Total Tests</dt>
          <dd>{metrics?.total_tests?.toLocaleString() ?? "—"}</dd>
        </div>
        <div>
          <dt className="text-[var(--muted)]">Pass / Fail / Skipped</dt>
          <dd>
            {metrics
              ? `${metrics.total_passed} / ${metrics.total_failed} / ${Math.max(0, metrics.total_tests - metrics.total_passed - metrics.total_failed)}`
              : "—"}
          </dd>
        </div>
        <div>
          <dt className="text-[var(--muted)]">Records Accepted</dt>
          <dd>{String(dataset?.records_accepted ?? upload?.records_accepted ?? "—")}</dd>
        </div>
        <div>
          <dt className="text-[var(--muted)]">Status</dt>
          <dd>{String(dataset?.status || upload?.status || "—")}</dd>
        </div>
      </dl>
    </div>
  );
});
