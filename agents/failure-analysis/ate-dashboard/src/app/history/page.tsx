"use client";

import { UploadHistory } from "@/components/UploadHistory";
import { UploadQueue } from "@/components/UploadQueue";
import { AnalysisHistoryTable } from "@/components/workbench/AnalysisHistoryTable";

export default function HistoryPage() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Analysis History</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Pipeline execution history, upload processing status, and one-click reopen for prior
          analyses.
        </p>
      </header>

      <AnalysisHistoryTable />

      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
          Upload Jobs
        </h2>
        <div className="grid gap-4 xl:grid-cols-[320px_1fr]">
          <UploadQueue />
          <UploadHistory />
        </div>
      </section>
    </div>
  );
}
