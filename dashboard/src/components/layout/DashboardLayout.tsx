"use client";

import { useRef } from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopNavbar } from "@/components/layout/TopNavbar";
import { MobileSidebarOverlay } from "@/components/layout/MobileSidebarOverlay";
import { AuthGuard } from "@/components/providers/AuthGuard";

interface DashboardLayoutProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  hideQuickFilters?: boolean;
  searchPlaceholder?: string;
  primaryActionLabel?: string;
  pageId?: string;
}

export function DashboardLayout({
  children,
  title,
  subtitle,
  hideQuickFilters,
  searchPlaceholder,
  primaryActionLabel,
  pageId = "dashboard",
}: DashboardLayoutProps) {
  const contentRef = useRef<HTMLElement>(null);

  return (
    <AuthGuard>
      <div className="dashboard-shell">
      <Sidebar hideQuickFilters={hideQuickFilters} />
      <MobileSidebarOverlay hideQuickFilters={hideQuickFilters} />
      <TopNavbar
        title={title}
        subtitle={subtitle}
        searchPlaceholder={searchPlaceholder}
        primaryActionLabel={primaryActionLabel}
        pageId={pageId}
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
    </AuthGuard>
  );
}
