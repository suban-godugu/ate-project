"use client";

import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, X } from "lucide-react";

interface SettingsToastProps {
  message: string;
  visible: boolean;
  onClose: () => void;
}

export function SettingsToast({ message, visible, onClose }: SettingsToastProps) {
  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, y: 40, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 20, scale: 0.95 }}
          transition={{ type: "spring", bounce: 0.3 }}
          className="fixed bottom-8 left-1/2 z-50 flex -translate-x-1/2 items-center gap-3 rounded-2xl border border-emerald-500/30 bg-[#111827]/95 px-6 py-4 shadow-2xl shadow-emerald-500/10 backdrop-blur-xl"
        >
          <CheckCircle2 className="h-5 w-5 text-emerald-400" />
          <span className="text-sm font-medium text-white">{message}</span>
          <button
            type="button"
            onClick={onClose}
            className="ml-2 text-slate-400 hover:text-white"
          >
            <X className="h-4 w-4" />
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
