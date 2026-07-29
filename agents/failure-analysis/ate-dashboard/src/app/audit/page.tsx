"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export default function AuditPage() {
  const [search, setSearch] = useState("");
  const [action, setAction] = useState("");

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["audit", search, action],
    queryFn: async () => {
      const { data } = await api.get("/audit", {
        params: {
          search: search || undefined,
          action: action || undefined,
          limit: 200,
        },
      });
      return data as {
        events: Array<{
          id: string;
          action: string;
          actor_email?: string | null;
          resource_type?: string | null;
          resource_id?: string | null;
          ip_address?: string | null;
          created_at?: string | null;
          details?: Record<string, unknown>;
        }>;
      };
    },
  });

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Audit Logs</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Login, logout, uploads, analysis, reports, settings, and user management events.
        </p>
      </header>

      <div className="flex flex-wrap gap-2">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search actor / action…"
          className="rounded-xl border border-white/10 bg-black/25 px-3 py-2 text-sm"
          aria-label="Search audit logs"
        />
        <select
          value={action}
          onChange={(e) => setAction(e.target.value)}
          className="rounded-xl border border-white/10 bg-black/25 px-3 py-2 text-sm"
          aria-label="Filter by action"
        >
          <option value="">All actions</option>
          {[
            "login",
            "logout",
            "login_failed",
            "user_created",
            "user_updated",
            "user_disabled",
            "user_deleted",
            "password_reset",
            "settings_changed",
            "file_archived",
            "file_deleted",
          ].map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={() => refetch()}
          className="rounded-xl border border-white/10 px-3 py-2 text-sm hover:bg-white/5"
        >
          Refresh
        </button>
      </div>

      <div className="glass-panel overflow-hidden rounded-2xl" data-testid="audit-table">
        <div className="max-h-[640px] overflow-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-[var(--surface)]/95 text-xs uppercase text-[var(--muted)]">
              <tr>
                <th className="px-4 py-3 text-left">Time</th>
                <th className="px-4 py-3 text-left">Action</th>
                <th className="px-4 py-3 text-left">Actor</th>
                <th className="px-4 py-3 text-left">Resource</th>
                <th className="px-4 py-3 text-left">IP</th>
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-[var(--muted)]">
                    Loading audit events…
                  </td>
                </tr>
              )}
              {(data?.events || []).map((e) => (
                <tr key={e.id} className="border-t border-white/5">
                  <td className="px-4 py-2 text-xs">
                    {e.created_at ? new Date(e.created_at).toLocaleString() : "—"}
                  </td>
                  <td className="px-4 py-2 font-mono text-xs">{e.action}</td>
                  <td className="px-4 py-2">{e.actor_email || "—"}</td>
                  <td className="px-4 py-2 text-xs">
                    {e.resource_type || "—"}
                    {e.resource_id ? ` · ${e.resource_id.slice(0, 8)}` : ""}
                  </td>
                  <td className="px-4 py-2 font-mono text-xs">{e.ip_address || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
