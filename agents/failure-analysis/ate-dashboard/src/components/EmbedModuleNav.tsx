"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BrainCircuit,
  CircleDot,
  Cpu,
  Database,
  FileText,
  GitFork,
  HardDrive,
  History,
  LayoutDashboard,
  Percent,
  Repeat2,
  ScanSearch,
  Settings,
  Shield,
  Users,
  HeartPulse,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { canAccessRoute } from "@/lib/rbac";
import { useAuthStore } from "@/stores/authStore";
import { appConfig } from "@/lib/config";
import { useEmbedMode, withEmbedQuery } from "@/hooks/useEmbedMode";

const links = [
  { href: "/overview", label: "Overview", icon: LayoutDashboard },
  // Local Ingestion removed in VERILUMEN embed — use platform Upload Data / Upload Log (parser).
  { href: "/datasets", label: "Datasets", icon: Database },
  { href: "/patterns", label: "Patterns", icon: ScanSearch },
  { href: "/failure-rates", label: "Rates", icon: Percent },
  { href: "/recurrence", label: "Recurring", icon: Repeat2 },
  { href: "/correlation", label: "Correlation", icon: GitFork },
  { href: "/die-analysis", label: "Die", icon: Cpu },
  { href: "/wafer-analysis", label: "Wafer", icon: CircleDot },
  { href: "/fault-prediction", label: "Prediction", icon: BrainCircuit },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/history", label: "History", icon: History },
  { href: "/stats", label: "Stats", icon: Activity },
  { href: "/storage", label: "Storage", icon: HardDrive },
  { href: "/system-health", label: "Health", icon: HeartPulse },
  { href: "/audit", label: "Audit", icon: Shield },
  { href: "/users", label: "Users", icon: Users },
  { href: "/settings", label: "Settings", icon: Settings },
];

/** Compact in-module nav for VERILUMEN platform embed (no separate product chrome). */
export function EmbedModuleNav() {
  const pathname = usePathname();
  const embed = useEmbedMode();
  const role = useAuthStore((s) => s.user?.role);

  const visible = links.filter((l) => {
    if (!appConfig.authEnabled) return true;
    if (!role) return l.href === "/overview";
    return canAccessRoute(role, l.href);
  });

  return (
    <nav
      className="mb-4 flex gap-1 overflow-x-auto border-b border-[var(--border)] pb-2"
      aria-label="Failure analysis sections"
    >
      {visible.map(({ href, label, icon: Icon }) => {
        const active =
          href === "/overview"
            ? pathname === "/overview" || pathname === "/"
            : pathname.startsWith(href);
        return (
          <Link
            key={href}
            href={withEmbedQuery(href, embed)}
            className={cn(
              "inline-flex shrink-0 items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs transition-colors",
              active
                ? "bg-[var(--accent-soft)] font-semibold text-white"
                : "text-[var(--muted)] hover:bg-white/5 hover:text-white",
            )}
          >
            <Icon size={13} aria-hidden="true" />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
