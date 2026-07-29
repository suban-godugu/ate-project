"use client";

import { memo, useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchWorkbenchLogs } from "@/services/workbench";

function severityClass(status?: string, message?: string) {
  const s = `${status || ""} ${message || ""}`.toUpperCase();
  if (s.includes("FAIL") || s.includes("ERROR")) return "text-[var(--danger)]";
  if (s.includes("WARN")) return "text-[var(--warning)]";
  if (s.includes("PASS") || s.includes("SUCCESS")) return "text-[var(--success)]";
  return "text-sky-300";
}

type Props = { executionId?: string | null };

export const LiveLogsPanel = memo(function LiveLogsPanel({ executionId }: Props) {
  const [search, setSearch] = useState("");
  const [severity, setSeverity] = useState<string>("all");
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["workbench-logs", executionId],
    queryFn: () => fetchWorkbenchLogs(executionId || undefined),
    enabled: Boolean(executionId),
    refetchInterval: executionId ? 3000 : false,
  });

  const logs = useMemo(() => {
    let rows = data?.logs || [];
    if (severity !== "all") {
      rows = rows.filter((l) =>
        `${l.status} ${l.message}`.toUpperCase().includes(severity.toUpperCase()),
      );
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      rows = rows.filter(
        (l) =>
          l.message?.toLowerCase().includes(q) ||
          l.module?.toLowerCase().includes(q),
      );
    }
    return rows;
  }, [data, search, severity]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs.length]);

  return (
    <div className="glass-panel rounded-2xl p-4" data-testid="live-logs">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
          Live Logs
        </h3>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search logs…"
          className="ml-auto rounded-lg border border-white/10 bg-black/25 px-2 py-1 text-xs"
        />
        <select
          value={severity}
          onChange={(e) => setSeverity(e.target.value)}
          className="rounded-lg border border-white/10 bg-black/25 px-2 py-1 text-xs"
        >
          <option value="all">All</option>
          <option value="INFO">INFO</option>
          <option value="WARNING">WARNING</option>
          <option value="ERROR">ERROR</option>
          <option value="PASS">SUCCESS</option>
        </select>
      </div>
      <div className="max-h-64 overflow-auto rounded-xl bg-black/30 p-2 font-mono text-xs">
        {isLoading && <p className="text-[var(--muted)]">Streaming logs…</p>}
        {!isLoading && !logs.length && (
          <p className="text-[var(--muted)]">No logs for this execution yet.</p>
        )}
        {logs.map((log, i) => (
          <div key={`${log.timestamp}-${i}`} className="border-b border-white/5 py-1">
            <span className="text-[var(--muted)]">{log.timestamp?.slice(11, 19) || "—"} </span>
            <span className="text-[var(--accent)]">[{log.module || "—"}] </span>
            <span className={severityClass(log.status, log.message)}>{log.status || "INFO"}</span>
            <span className="text-[var(--foreground)]"> — {log.message}</span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
});
