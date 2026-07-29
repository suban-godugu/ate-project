"use client";

import { useQuery } from "@tanstack/react-query";
import { getUpload, listUploads } from "@/lib/api";
import { useUploadStore } from "@/store/upload-store";
import { cn } from "@/lib/utils";

export function UploadHistory() {
  const selected = useUploadStore((s) => s.selectedUploadId);
  const setSelected = useUploadStore((s) => s.setSelectedUploadId);
  const { data, isLoading } = useQuery({
    queryKey: ["uploads"],
    queryFn: listUploads,
    refetchInterval: 4000,
  });

  return (
    <div className="glass-panel overflow-hidden rounded-2xl">
      <div className="border-b border-white/5 px-4 py-3 text-sm font-semibold tracking-wide text-[var(--muted)] uppercase">
        Upload History
      </div>
      <div className="max-h-[420px] overflow-auto">
        <table className="w-full text-left text-sm">
          <thead className="sticky top-0 bg-[#111827]/90 text-[11px] uppercase tracking-wide text-[var(--muted)]">
            <tr>
              <th className="px-4 py-2">File</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">Parser</th>
              <th className="px-4 py-2">Accepted</th>
              <th className="px-4 py-2">Integrity</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-[var(--muted)]">
                  Loading…
                </td>
              </tr>
            )}
            {(data?.uploads || []).map((u) => (
              <tr
                key={u.id}
                onClick={() => setSelected(u.id)}
                className={cn(
                  "cursor-pointer border-t border-white/5 hover:bg-white/5",
                  selected === u.id && "bg-[var(--accent-soft)]",
                )}
              >
                <td className="px-4 py-3 font-medium">{u.original_filename}</td>
                <td className="px-4 py-3">
                  <span className="rounded-full bg-white/5 px-2 py-0.5 text-xs">{u.status}</span>
                </td>
                <td className="px-4 py-3 text-[var(--muted)]">{u.parser_id || "—"}</td>
                <td className="px-4 py-3">{u.records_accepted ?? 0}</td>
                <td className="px-4 py-3">{(u.integrity_pct ?? 0).toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {selected && <ValidationPanel uploadId={selected} />}
    </div>
  );
}

function ValidationPanel({ uploadId }: { uploadId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ["upload", uploadId],
    queryFn: () => getUpload(uploadId),
    refetchInterval: 3000,
  });

  if (isLoading || !data) {
    return <div className="border-t border-white/5 p-4 text-sm text-[var(--muted)]">Loading validation…</div>;
  }

  return (
    <div className="grid gap-4 border-t border-white/5 p-4 md:grid-cols-2">
      <div>
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
          Validation Report
        </h4>
        <pre className="max-h-56 overflow-auto rounded-xl bg-black/30 p-3 text-xs text-[var(--muted)]">
          {JSON.stringify(data.upload.validation_report || {}, null, 2)}
        </pre>
      </div>
      <div>
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
          Error Viewer
        </h4>
        {data.validation_results?.length ? (
          <ul className="max-h-56 space-y-2 overflow-auto">
            {data.validation_results.map((v, i) => (
              <li
                key={i}
                className={cn(
                  "rounded-lg border px-3 py-2 text-xs",
                  v.severity === "error"
                    ? "border-red-500/30 bg-red-500/10 text-red-200"
                    : "border-amber-500/30 bg-amber-500/10 text-amber-100",
                )}
              >
                <div className="font-semibold">
                  {v.code} · {v.category}
                </div>
                <div>{v.message}</div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-[var(--muted)]">
            {data.upload.error_message || "No validation errors."}
          </p>
        )}
      </div>
    </div>
  );
}
