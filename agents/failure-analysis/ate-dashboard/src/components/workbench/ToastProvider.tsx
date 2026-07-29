"use client";

import { memo, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";
import { useToastStore, type ToastVariant } from "@/stores/toastStore";
import { cn } from "@/lib/utils";

const VARIANT_STYLES: Record<ToastVariant, string> = {
  default: "border-white/15 bg-[var(--surface)]/95",
  success: "border-[var(--success)]/40 bg-emerald-950/80",
  warning: "border-[var(--warning)]/40 bg-amber-950/80",
  error: "border-[var(--danger)]/40 bg-red-950/80",
  info: "border-sky-500/40 bg-sky-950/80",
};

export const ToastProvider = memo(function ToastProvider() {
  const toasts = useToastStore((s) => s.toasts);
  const dismiss = useToastStore((s) => s.dismiss);

  useEffect(() => {
    if (!toasts.length) return;
    const timers = toasts.map((t) =>
      window.setTimeout(() => dismiss(t.id), 6000),
    );
    return () => timers.forEach(clearTimeout);
  }, [toasts, dismiss]);

  return (
    <div
      className="pointer-events-none fixed bottom-4 right-4 z-[100] flex w-full max-w-sm flex-col gap-2"
      data-testid="toast-provider"
    >
      <AnimatePresence>
        {toasts.map((toast) => (
          <motion.div
            key={toast.id}
            initial={{ opacity: 0, y: 16, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, x: 24 }}
            className={cn(
              "pointer-events-auto rounded-xl border p-4 shadow-xl backdrop-blur-md",
              VARIANT_STYLES[toast.variant],
            )}
          >
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="text-sm font-semibold">{toast.title}</p>
                {toast.description && (
                  <p className="mt-1 text-xs text-[var(--muted)]">{toast.description}</p>
                )}
              </div>
              <button
                type="button"
                onClick={() => dismiss(toast.id)}
                className="rounded-md p-1 hover:bg-white/10"
                aria-label="Dismiss"
              >
                <X size={14} />
              </button>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
});
