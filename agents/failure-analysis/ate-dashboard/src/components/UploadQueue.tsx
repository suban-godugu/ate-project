"use client";

import { useUploadStore } from "@/store/upload-store";
import { cn } from "@/lib/utils";

export function UploadQueue() {
  const queue = useUploadStore((s) => s.queue);
  const clearCompleted = useUploadStore((s) => s.clearCompleted);

  return (
    <div className="glass-panel rounded-2xl p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold tracking-wide text-[var(--muted)] uppercase">
          Upload Queue
        </h3>
        <button
          type="button"
          onClick={clearCompleted}
          className="text-xs text-[var(--accent)] hover:underline"
        >
          Clear completed
        </button>
      </div>
      {queue.length === 0 ? (
        <p className="text-sm text-[var(--muted)]">No active uploads.</p>
      ) : (
        <div className="space-y-3">
          {queue.map((item) => (
            <div key={item.id} className="rounded-xl border border-white/5 bg-black/20 p-3">
              <div className="mb-2 flex items-center justify-between gap-3">
                <div className="truncate text-sm">{item.name}</div>
                <span
                  className={cn(
                    "rounded-full px-2 py-0.5 text-[10px] uppercase tracking-wide",
                    item.status === "completed" && "bg-emerald-500/15 text-emerald-300",
                    item.status === "failed" && "bg-red-500/15 text-red-300",
                    item.status === "processing" && "bg-violet-500/15 text-violet-300",
                    item.status === "uploading" && "bg-sky-500/15 text-sky-300",
                    item.status === "queued" && "bg-white/10 text-[var(--muted)]",
                  )}
                >
                  {item.status}
                </span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-white/10">
                <div
                  className="h-full rounded-full bg-[var(--accent)] transition-all"
                  style={{ width: `${item.progress}%` }}
                />
              </div>
              {item.error && <p className="mt-2 text-xs text-red-300">{item.error}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
