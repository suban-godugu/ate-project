"use client";

import { Activity, Moon, Sun, Wifi, WifiOff } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

import { useAnalysis } from "@/context/AnalysisContext";
import { cn } from "@/utils/format";

export function TopNav() {
  const { theme, setTheme } = useTheme();
  const { connectionStatus, isAnalyzing } = useAnalysis();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const online = connectionStatus === "connected";
  const offline =
    connectionStatus === "offline" || connectionStatus === "backend_error";

  let statusLabel = "API Idle";
  if (isAnalyzing) statusLabel = "Analyzing…";
  else if (connectionStatus === "connected") statusLabel = "API Connected";
  else if (connectionStatus === "offline") statusLabel = "API Offline";
  else if (connectionStatus === "backend_error") statusLabel = "Backend Error";

  return (
    <header className="panel sticky top-0 z-40 mb-6 flex flex-wrap items-center justify-between gap-4 px-5 py-4">
      <div className="flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-ink-800 text-white dark:bg-ink-200 dark:text-ink-900">
          <Activity className="h-5 w-5" />
        </div>
        <div>
          <p className="font-display text-xl font-semibold tracking-tight">
            WaferVision-AI
          </p>
          <p className="text-xs uppercase tracking-[0.16em] text-[var(--muted)]">
            Semiconductor Inspection Dashboard
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div
          className={cn(
            "inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium",
            online
              ? "border-signal-good/30 bg-signal-good/10 text-signal-good"
              : offline
                ? "border-signal-fail/30 bg-signal-fail/10 text-signal-fail"
                : "border-[var(--line)] text-[var(--muted)]",
          )}
        >
          {offline ? (
            <WifiOff className="h-3.5 w-3.5" />
          ) : (
            <Wifi className="h-3.5 w-3.5" />
          )}
          {statusLabel}
        </div>

        <button
          type="button"
          aria-label="Toggle theme"
          className="rounded-lg border border-[var(--line)] px-3 py-2 text-sm hover:bg-ink-100 dark:hover:bg-ink-800"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
        >
          {mounted && theme === "dark" ? (
            <Sun className="h-4 w-4" />
          ) : (
            <Moon className="h-4 w-4" />
          )}
        </button>
      </div>
    </header>
  );
}
