"use client";

import { StatsPanel } from "@/components/StatsPanel";

export default function StatsPage() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Parser Statistics</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Ingestion throughput, parser distribution, and processing status.
        </p>
      </header>
      <StatsPanel />
    </div>
  );
}
