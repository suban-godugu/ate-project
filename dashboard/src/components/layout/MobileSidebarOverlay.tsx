"use client";

import { motion, AnimatePresence } from "framer-motion";
import { SidebarNav } from "@/components/layout/SidebarNav";
import { useUIStore } from "@/stores/uiStore";

interface MobileSidebarOverlayProps {
  hideQuickFilters?: boolean;
}

export function MobileSidebarOverlay({ hideQuickFilters }: MobileSidebarOverlayProps) {
  const open = useUIStore((s) => s.mobileSidebarOpen);
  const setOpen = useUIStore((s) => s.setMobileSidebarOpen);

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.button
            type="button"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 bg-black/60 lg:hidden"
            aria-label="Close navigation overlay"
            onClick={() => setOpen(false)}
          />
          <motion.aside
            initial={{ x: -300 }}
            animate={{ x: 0 }}
            exit={{ x: -300 }}
            transition={{ type: "spring", damping: 28, stiffness: 280 }}
            className="dashboard-sidebar fixed left-0 top-0 z-50 flex h-full w-[280px] flex-col border-r border-[#1e293b] bg-[#0A1020] lg:hidden"
          >
            <SidebarNav hideQuickFilters={hideQuickFilters} onNavigate={() => setOpen(false)} mobile />
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}
