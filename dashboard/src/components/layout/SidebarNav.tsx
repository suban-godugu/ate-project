"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  AlertTriangle,
  Binary,
  ChevronLeft,
  ChevronRight,
  Cpu,
  DollarSign,
  LayoutDashboard,
  Microscope,
  RotateCcw,
  ScanLine,
  Settings,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { FILTER_OPTIONS } from "@/types/platform";
import { useFilterStore } from "@/stores/filterStore";
import { useUIStore } from "@/stores/uiStore";
import { useQueryClient } from "@tanstack/react-query";
import { cn } from "@/lib/utils";

const navItems = [
  { id: "dashboard", href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "scan-chain", href: "/dashboard/scan-chain", label: "Scan Chain Analysis", icon: ScanLine },
  { id: "mbist", href: "/dashboard/mbist", label: "MBIST Analysis", icon: Cpu },
  { id: "lbist", href: "/dashboard/lbist", label: "LBIST Analysis", icon: Binary },
  { id: "wafervision", href: "/dashboard/wafervision", label: "WaferVision", icon: Microscope },
  { id: "cost", href: "/dashboard/cost-intelligence", label: "Cost Intelligence", icon: DollarSign },
  { id: "recommendation-analysis", href: "/dashboard/recommendation-analysis", label: "Recommendation Analysis", icon: Sparkles },
  { id: "alerts", href: "/dashboard/alerts", label: "Alerts", icon: AlertTriangle },
];

interface SidebarNavProps {
  hideQuickFilters?: boolean;
  onNavigate?: () => void;
  mobile?: boolean;
}

export function SidebarNav({ hideQuickFilters, onNavigate, mobile }: SidebarNavProps) {
  const pathname = usePathname();
  const filters = useFilterStore((s) => s.filters);
  const setFilters = useFilterStore((s) => s.setFilters);
  const resetFilters = useFilterStore((s) => s.resetFilters);
  const sidebarCollapsed = useUIStore((s) => s.sidebarCollapsed);
  const toggleSidebarCollapsed = useUIStore((s) => s.toggleSidebarCollapsed);
  const queryClient = useQueryClient();

  const updateFilter = (key: keyof typeof filters, value: string) => {
    setFilters({ [key]: value });
    // Only refresh dashboard queries — avoid wiping the entire cache.
    void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
  };

  const handleReset = () => {
    resetFilters();
    void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
  };

  const isNavActive = (href: string) => {
    if (href === "/dashboard") return pathname === "/dashboard";
    return pathname.startsWith(href);
  };

  return (
    <>
      <div className="flex items-center gap-3 border-b border-[#1e293b] px-5 py-5">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#7C3AED] shadow-lg shadow-purple-500/20">
          <Cpu className="h-5 w-5 text-white" />
        </div>
        {!sidebarCollapsed && (
          <div>
            <p className="text-sm font-semibold text-white">ATE Intelligence</p>
            <p className="text-xs text-slate-400">Enterprise Platform</p>
          </div>
        )}
        {!mobile && (
          <Button
            variant="ghost"
            size="icon"
            className="ml-auto hidden h-8 w-8 rounded-lg text-slate-400 xl:flex"
            onClick={toggleSidebarCollapsed}
            aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {sidebarCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
        )}
      </div>

      <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-4" aria-label="Main navigation">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = isNavActive(item.href);
          const isRecommendation = item.id === "recommendation-analysis";

          const linkClassName = cn(
            "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#7C3AED]/50 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0A1020]",
            isRecommendation ? "text-base" : "text-sm",
            sidebarCollapsed && !mobile && "justify-center px-2",
            active
              ? cn(
                  "bg-gradient-to-r text-white shadow-md shadow-purple-500/30 ring-1 ring-[#7C3AED]/40",
                  isRecommendation ? "from-[#7C3AED] to-[#8B5CF6]" : "from-[#7C3AED] to-[#5B21B6]"
                )
              : cn(
                  "text-slate-400",
                  isRecommendation
                    ? "hover:scale-[1.02] hover:bg-[#7C3AED]/10 hover:text-white hover:shadow-md hover:shadow-purple-500/20 duration-[250ms]"
                    : "hover:bg-white/5 hover:text-white"
                )
          );

          const link = (
            <Link
              href={item.href}
              className={linkClassName}
              aria-label={item.label}
              aria-current={active ? "page" : undefined}
              title={item.label}
              onClick={onNavigate}
            >
              <Icon className={cn("shrink-0", isRecommendation ? "h-5 w-5" : "h-4 w-4", active ? "text-white" : "text-slate-400 group-hover:text-white")} aria-hidden="true" />
              {(!sidebarCollapsed || mobile) && <span className="flex-1">{item.label}</span>}
            </Link>
          );

          if (isRecommendation) {
            return (
              <motion.div key={item.id} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.25 }}>
                {link}
              </motion.div>
            );
          }
          return <div key={item.id}>{link}</div>;
        })}

        <div className="my-3 border-t border-[#1e293b]" />

        <Link
          href="/dashboard/settings"
          onClick={onNavigate}
          className={cn(
            "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#7C3AED]/50",
            pathname === "/dashboard/settings"
              ? "bg-[#7C3AED] text-white shadow-md shadow-purple-500/25"
              : "text-slate-400 hover:bg-white/5 hover:text-white",
            sidebarCollapsed && !mobile && "justify-center px-2"
          )}
        >
          <Settings className="h-4 w-4" />
          {(!sidebarCollapsed || mobile) && "Settings"}
        </Link>
      </nav>

      {!hideQuickFilters && (!sidebarCollapsed || mobile) && (
        <div className="border-t border-[#1e293b] p-3">
          <div className="glass-card rounded-lg p-3">
            <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-400">Quick Filters</p>
            <div className="grid grid-cols-2 gap-2">
              {(
                [
                  ["fab", "Fab", FILTER_OPTIONS.fab],
                  ["tester", "Tester", FILTER_OPTIONS.tester],
                  ["product", "Product", FILTER_OPTIONS.product],
                  ["lot", "Lot", FILTER_OPTIONS.lot],
                  ["wafer", "Wafer", FILTER_OPTIONS.wafer],
                ] as const
              ).map(([key, label, options]) => (
                <div key={key} className={key === "lot" || key === "wafer" ? "" : ""}>
                  <label className="mb-0.5 block text-[10px] text-slate-500">{label}</label>
                  <Select value={filters[key]} onValueChange={(v) => updateFilter(key, v ?? filters[key])}>
                    <SelectTrigger className="h-7 w-full border-[#2D3748] bg-[#0A1020] px-2 text-[11px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {options.map((opt) => (
                        <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              ))}
              <Button variant="outline" size="sm" className="col-span-2 h-7 w-full border-[#2D3748] text-[11px] hover:border-[#7C3AED]" onClick={handleReset}>
                <RotateCcw className="mr-1 h-3 w-3" />
                Reset Filters
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
