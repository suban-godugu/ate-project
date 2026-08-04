"use client";

import { useSearchParams } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const searchParams = useSearchParams();
  const embedMode = searchParams?.get("embed") === "1";

  // Keep the agent sidebar visible in the VERILUMEN iframe (same as standalone).
  return (
    <div
      className={`flex overflow-x-hidden bg-[#090b12] ${
        embedMode ? "h-[100dvh] max-h-[100dvh]" : "min-h-screen"
      }`}
    >
      <Sidebar />
      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <Header
          title="Scan Debug Recommendation Agent"
          subtitle="AI decision workspace for semiconductor scan chain debugging"
        />
        <main
          className={`min-h-0 flex-1 overflow-x-hidden overflow-y-auto ${
            embedMode ? "px-2 py-2 md:px-3" : "px-4 py-6 md:px-6"
          }`}
        >
          {children}
        </main>
      </div>
    </div>
  );
}
