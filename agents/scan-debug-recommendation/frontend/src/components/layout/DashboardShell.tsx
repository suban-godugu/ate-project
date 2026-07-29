"use client";

import { useSearchParams } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const searchParams = useSearchParams();
  const embedMode = searchParams?.get("embed") === "1";

  if (embedMode) {
    return (
      <div className="min-h-screen bg-[#090b12]">
        <main className="flex-1 px-0 py-0">{children}</main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Header
          title="Scan Debug Recommendation Agent"
          subtitle="AI decision workspace for semiconductor scan chain debugging"
        />
        <main className="flex-1 px-4 py-6 md:px-6">{children}</main>
      </div>
    </div>
  );
}
