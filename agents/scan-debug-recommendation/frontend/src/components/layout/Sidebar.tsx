"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  LayoutDashboard,
  Settings,
  Sparkles,
} from "lucide-react";

const NAV = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  {
    href: "/dashboard/recommendation-analysis",
    label: "Scan Debug Recommendation Agent",
    icon: Activity,
  },
  { href: "#", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="flex w-52 shrink-0 flex-col border-r border-border/80 bg-[#0B0F1A]/90 px-2.5 py-3 backdrop-blur-xl">
      <div className="mb-8 flex items-center gap-2 px-2">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary/20 text-primary">
          <Sparkles size={18} />
        </div>
        <div>
          <div className="font-display text-sm font-semibold tracking-wide text-white">
            COMPTY
          </div>
          <div className="text-[10px] uppercase tracking-[0.16em] text-muted">
            VERILUMEN · ATE Yield
          </div>
        </div>
      </div>
      <nav className="flex flex-1 flex-col gap-1">
        {NAV.map((item) => {
          const active = pathname.startsWith(item.href) && item.href !== "#";
          const Icon = item.icon;
          return (
            <Link
              key={item.label}
              href={item.href}
              className={`flex items-center gap-2 rounded-xl px-3 py-2.5 text-sm transition ${
                active
                  ? "bg-primary/20 text-white"
                  : "text-slate-400 hover:bg-white/5 hover:text-white"
              }`}
            >
              <Icon size={16} />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="mt-auto rounded-xl border border-border/70 bg-card/60 p-3 text-[11px] text-muted">
        Scan Debug Recommendation Agent · Enterprise DFT
      </div>
    </aside>
  );
}
