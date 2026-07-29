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
  FolderUp,
  GitFork,
  HardDrive,
  History,
  LayoutDashboard,
  Percent,
  Repeat2,
  ScanSearch,
  Settings,
  Shield,
  UploadCloud,
  Users,
  HeartPulse,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { canAccessRoute } from "@/lib/rbac";
import { useAuthStore } from "@/stores/authStore";
import { appConfig } from "@/lib/config";

const links = [
  { href: "/overview", label: "Overview", icon: LayoutDashboard },
  { href: "/upload", label: "Ingestion", icon: UploadCloud },
  { href: "/datasets", label: "Datasets", icon: Database },
  { href: "/patterns", label: "Pattern Detection", icon: ScanSearch },
  { href: "/failure-rates", label: "Failure Rates", icon: Percent },
  { href: "/recurrence", label: "Recurring Failures", icon: Repeat2 },
  { href: "/correlation", label: "Correlation", icon: GitFork },
  { href: "/die-analysis", label: "Die Analysis", icon: Cpu },
  { href: "/wafer-analysis", label: "Wafer Analysis", icon: CircleDot },
  { href: "/fault-prediction", label: "Fault Prediction", icon: BrainCircuit },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/history", label: "History", icon: History },
  { href: "/stats", label: "Statistics", icon: Activity },
  { href: "/storage", label: "Storage", icon: HardDrive },
  { href: "/system-health", label: "System Health", icon: HeartPulse },
  { href: "/audit", label: "Audit Logs", icon: Shield },
  { href: "/users", label: "Users", icon: Users },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const role = useAuthStore((s) => s.user?.role);

  const visible = links.filter((l) => {
    if (!appConfig.authEnabled) return true;
    if (!role) return l.href === "/overview";
    return canAccessRoute(role, l.href);
  });

  return (
    <aside
      className="glass-panel flex w-64 shrink-0 flex-col rounded-2xl p-4"
      aria-label="Primary navigation"
    >
      <div className="mb-8 px-2">
        <div className="text-xs font-semibold tracking-[0.25em] text-[var(--accent)]">
          ATE DASHBOARD
        </div>
        <div className="mt-1 text-sm text-[var(--muted)]">FA-FR-001 → 010</div>
      </div>
      <nav className="flex flex-1 flex-col gap-1" aria-label="Modules">
        {visible.map(({ href, label, icon: Icon }) => {
          const active =
            href === "/overview"
              ? pathname === "/overview" || pathname === "/"
              : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              prefetch
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--accent)]",
                active
                  ? "bg-[var(--accent-soft)] text-white accent-ring"
                  : "text-[var(--muted)] hover:bg-white/5 hover:text-white",
              )}
            >
              <Icon size={16} aria-hidden />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="mt-4 rounded-xl border border-white/10 bg-black/20 p-3 text-xs text-[var(--muted)]">
        <div className="mb-1 flex items-center gap-2 text-white">
          <FolderUp size={14} aria-hidden /> Enterprise Glass Theme
        </div>
        FastAPI → PostgreSQL → Downstream FA modules
      </div>
    </aside>
  );
}
