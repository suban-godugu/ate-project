"use client";

import { AnimatePresence, motion } from "framer-motion";
import { AlertCircle, CheckCircle2, Info, X } from "lucide-react";
import { useUpload } from "@/contexts/UploadContext";

const icons = {
  success: CheckCircle2,
  error: AlertCircle,
  info: Info,
};

const styles = {
  success: "border-emerald-500/30 text-emerald-400 shadow-emerald-500/10",
  error: "border-red-500/30 text-red-400 shadow-red-500/10",
  info: "border-cyan-500/30 text-cyan-400 shadow-cyan-500/10",
};

export function UploadToastStack() {
  const { toasts, dismissToast } = useUpload();

  return (
    <div className="pointer-events-none fixed bottom-6 right-6 z-[100] flex flex-col gap-2">
      <AnimatePresence>
        {toasts.map((toast) => {
          const Icon = icons[toast.type];
          return (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, x: 40, scale: 0.95 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 20, scale: 0.95 }}
              className={`pointer-events-auto flex items-center gap-3 rounded-2xl border bg-[#111827]/95 px-4 py-3 shadow-2xl backdrop-blur-xl ${styles[toast.type]}`}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span className="text-sm font-medium text-white">{toast.message}</span>
              <button type="button" onClick={() => dismissToast(toast.id)} className="text-slate-400 hover:text-white">
                <X className="h-4 w-4" />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
