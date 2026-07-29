"use client";

import { useQuery } from "@tanstack/react-query";
import { listDatasets, getDataset, scanServerDataset } from "@/lib/api";
import { useState } from "react";
import { cn } from "@/lib/utils";

export default function DatasetsPage() {
  const [selected, setSelected] = useState<string | null>(null);
  const [scanName, setScanName] = useState("server_scan");
  const [scanning, setScanning] = useState(false);
  const [scanMsg, setScanMsg] = useState<string | null>(null);

  const { data, refetch, isLoading } = useQuery({
    queryKey: ["datasets"],
    queryFn: listDatasets,
    refetchInterval: 5000,
  });

  const detail = useQuery({
    queryKey: ["dataset", selected],
    queryFn: () => getDataset(selected!),
    enabled: Boolean(selected),
    refetchInterval: 4000,
  });

  async function runScan() {
    setScanning(true);
    setScanMsg(null);
    try {
      const result = await scanServerDataset(scanName);
      setScanMsg(`Dataset ${result.dataset_id || result.dataset?.id || "created"}`);
      await refetch();
    } catch (err) {
      setScanMsg(err instanceof Error ? err.message : "Scan failed");
    } finally {
      setScanning(false);
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Dataset Explorer</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Browse multi-file ingestion datasets (STIL + logs) and scan trusted server roots.
        </p>
      </header>

      <div className="glass-panel flex flex-wrap items-end gap-3 rounded-2xl p-4">
        <div>
          <label className="text-xs uppercase tracking-wide text-[var(--muted)]">Scan name</label>
          <input
            value={scanName}
            onChange={(e) => setScanName(e.target.value)}
            className="mt-1 block w-64 rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm"
          />
        </div>
        <button
          type="button"
          disabled={scanning}
          onClick={runScan}
          className="rounded-xl bg-[var(--accent)] px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {scanning ? "Scanning…" : "Scan Server Dataset Root"}
        </button>
        {scanMsg && <p className="text-sm text-[var(--muted)]">{scanMsg}</p>}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="glass-panel overflow-hidden rounded-2xl">
          <div className="border-b border-white/5 px-4 py-3 text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
            Datasets
          </div>
          <div className="max-h-[520px] overflow-auto">
            {isLoading && <p className="p-4 text-sm text-[var(--muted)]">Loading…</p>}
            {(data?.datasets || []).map(
              (d: {
                id: string;
                name: string;
                status: string;
                file_count: number;
                stil_count: number;
                log_count: number;
                records_accepted: number;
              }) => (
                <button
                  key={d.id}
                  type="button"
                  onClick={() => setSelected(d.id)}
                  className={cn(
                    "flex w-full items-start justify-between gap-3 border-t border-white/5 px-4 py-3 text-left hover:bg-white/5",
                    selected === d.id && "bg-[var(--accent-soft)]",
                  )}
                >
                  <div>
                    <div className="font-medium">{d.name}</div>
                    <div className="mt-1 text-xs text-[var(--muted)]">
                      {d.file_count} files · {d.stil_count} STIL · {d.log_count} logs ·{" "}
                      {d.records_accepted} records
                    </div>
                  </div>
                  <span className="rounded-full bg-white/5 px-2 py-0.5 text-xs">{d.status}</span>
                </button>
              ),
            )}
          </div>
        </div>

        <div className="glass-panel rounded-2xl p-4">
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
            Dataset Detail
          </h3>
          {!selected && <p className="text-sm text-[var(--muted)]">Select a dataset.</p>}
          {detail.data && (
            <div className="space-y-4">
              <pre className="overflow-auto rounded-xl bg-black/30 p-3 text-xs text-[var(--muted)]">
                {JSON.stringify(detail.data.dataset, null, 2)}
              </pre>
              <div className="space-y-2">
                {(detail.data.uploads || []).map(
                  (u: {
                    id: string;
                    original_filename: string;
                    status: string;
                    parser_id?: string;
                    records_accepted?: number;
                  }) => (
                    <div
                      key={u.id}
                      className="rounded-xl border border-white/5 bg-black/20 px-3 py-2 text-sm"
                    >
                      <div className="flex justify-between gap-2">
                        <span className="truncate font-medium">{u.original_filename}</span>
                        <span className="text-xs text-[var(--muted)]">{u.status}</span>
                      </div>
                      <div className="mt-1 text-xs text-[var(--muted)]">
                        {u.parser_id || "—"} · {u.records_accepted ?? 0} accepted
                      </div>
                    </div>
                  ),
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
