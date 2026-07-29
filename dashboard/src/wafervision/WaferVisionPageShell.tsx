"use client";

import { useRef } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopNavbar } from "@/components/layout/TopNavbar";
import { MobileSidebarOverlay } from "@/components/layout/MobileSidebarOverlay";

interface WaferVisionPageShellProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  searchPlaceholder?: string;
  primaryActionLabel?: string;
}

/**
 * WaferVision page chrome — same shell as dashboard, without AuthGuard.
 * Lets the Spatial Agent UI render when the API session restore is slow/down.
 */
export function WaferVisionPageShell({
  children,
  title = "WaferVision",
  subtitle,
  searchPlaceholder,
  primaryActionLabel = "Analyze Wafer",
}: WaferVisionPageShellProps) {
  const contentRef = useRef<HTMLElement>(null);

  return (
    <div className="dashboard-shell">
      <Sidebar hideQuickFilters />
      <MobileSidebarOverlay hideQuickFilters />
      <TopNavbar
        title={title}
        subtitle={subtitle}
        searchPlaceholder={searchPlaceholder}
        primaryActionLabel={primaryActionLabel}
        pageId="wafervision"
        contentRef={contentRef}
      />
      <main
        ref={contentRef}
        className="dashboard-main"
        data-export-title={title}
        tabIndex={-1}
      >
        {children}
      </main>
    </div>
  );
}
