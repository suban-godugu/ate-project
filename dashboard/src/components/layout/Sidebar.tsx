"use client";

import { SidebarNav } from "@/components/layout/SidebarNav";
import { useUIStore } from "@/stores/uiStore";
import { cn } from "@/lib/utils";

interface SidebarProps {
  hideQuickFilters?: boolean;
}

export function Sidebar({ hideQuickFilters }: SidebarProps) {
  const sidebarCollapsed = useUIStore((s) => s.sidebarCollapsed);

  return (
    <aside
      className={cn(
        "dashboard-sidebar hidden h-full flex-col border-r border-[#1e293b] bg-[#0A1020] lg:flex",
        sidebarCollapsed ? "w-[88px]" : "w-[280px]"
      )}
    >
      <SidebarNav hideQuickFilters={hideQuickFilters} />
    </aside>
  );
}
