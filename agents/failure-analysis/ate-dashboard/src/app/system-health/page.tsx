"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

function HealthCard({
  label,
  value,
  status,
}: {
  label: string;
  value: string;
  status?: "ok" | "warn" | "error";
}) {
  const color =
    status === "ok"
      ? "text-[var(--success)]"
      : status === "error"
        ? "text-[var(--danger)]"
        : status === "warn"
          ? "text-[var(--warning)]"
          : "";
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-4">
      <div className="text-xs text-[var(--muted)]">{label}</div>
      <div className={`mt-1 text-lg font-semibold ${color}`}>{value}</div>
    </div>
  );
}

export default function SystemHealthPage() {
  const { data, isLoading, dataUpdatedAt } = useQuery({
    queryKey: ["system-health"],
    queryFn: async () => {
      const { data } = await api.get("/system/health");
      return data as {
        backend_status: string;
        database_status: string;
        storage_status: string;
        cpu_usage: number | null;
        memory_usage: number | null;
        disk_usage: number | null;
        api_response_time_ms: number;
        last_successful_analysis: {
          execution_id?: string;
          status?: string;
          created_at?: string;
        } | null;
        queue_size: number;
        uploaded_file_count: number;
        checked_at: string;
      };
    },
    refetchInterval: 10_000,
  });

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">System Health</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Backend, database, storage, and runtime metrics — auto-refresh every 10 seconds.
        </p>
        {dataUpdatedAt ? (
          <p className="mt-1 text-xs text-[var(--muted)]">
            Last refresh {new Date(dataUpdatedAt).toLocaleTimeString()}
          </p>
        ) : null}
      </header>

      {isLoading && !data && (
        <p className="text-sm text-[var(--muted)]">Loading health metrics…</p>
      )}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3" data-testid="system-health">
        <HealthCard
          label="Backend Status"
          value={data?.backend_status || "—"}
          status={data?.backend_status === "ok" ? "ok" : "error"}
        />
        <HealthCard
          label="Database Status"
          value={data?.database_status || "—"}
          status={data?.database_status === "ok" ? "ok" : "error"}
        />
        <HealthCard
          label="Storage Status"
          value={data?.storage_status || "—"}
          status={data?.storage_status === "ok" ? "ok" : "warn"}
        />
        <HealthCard
          label="CPU Usage"
          value={data?.cpu_usage != null ? `${data.cpu_usage.toFixed(1)}%` : "—"}
        />
        <HealthCard
          label="Memory Usage"
          value={data?.memory_usage != null ? `${data.memory_usage.toFixed(1)}%` : "—"}
        />
        <HealthCard
          label="Disk Usage"
          value={data?.disk_usage != null ? `${data.disk_usage.toFixed(1)}%` : "—"}
        />
        <HealthCard
          label="API Response Time"
          value={data ? `${data.api_response_time_ms} ms` : "—"}
        />
        <HealthCard label="Queue Size" value={String(data?.queue_size ?? "—")} />
        <HealthCard
          label="Uploaded Files"
          value={String(data?.uploaded_file_count ?? "—")}
        />
      </div>

      <div className="glass-panel rounded-2xl p-4">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
          Last Successful Analysis
        </h2>
        {data?.last_successful_analysis ? (
          <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-3">
            <div>
              <dt className="text-[var(--muted)]">Execution</dt>
              <dd className="font-mono text-xs">
                {data.last_successful_analysis.execution_id}
              </dd>
            </div>
            <div>
              <dt className="text-[var(--muted)]">Status</dt>
              <dd>{data.last_successful_analysis.status}</dd>
            </div>
            <div>
              <dt className="text-[var(--muted)]">Created</dt>
              <dd>
                {data.last_successful_analysis.created_at
                  ? new Date(data.last_successful_analysis.created_at).toLocaleString()
                  : "—"}
              </dd>
            </div>
          </dl>
        ) : (
          <p className="mt-2 text-sm text-[var(--muted)]">No evaluation runs recorded yet.</p>
        )}
      </div>
    </div>
  );
}
