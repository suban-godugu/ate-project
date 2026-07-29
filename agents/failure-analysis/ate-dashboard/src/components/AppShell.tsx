"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/Sidebar";
import { AuthGuard } from "@/components/AuthGuard";
import { NotificationCenter } from "@/components/NotificationCenter";
import { TopBar } from "@/components/TopBar";
import { EmbedModuleNav } from "@/components/EmbedModuleNav";
import { useEmbedMode } from "@/hooks/useEmbedMode";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isLogin = pathname?.startsWith("/login");
  const embed = useEmbedMode();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setReady(true);
  }, []);

  if (isLogin) {
    return <AuthGuard>{children}</AuthGuard>;
  }

  // Avoid one-frame flash of full sidebar/topbar inside VERILUMEN iframe.
  if (!ready) {
    return (
      <div className="min-h-screen bg-[var(--background)]" aria-hidden="true" />
    );
  }

  if (embed) {
    return (
      <AuthGuard>
        <div className="min-h-screen bg-[var(--background)] px-1 py-2 md:px-2">
          <EmbedModuleNav />
          <main id="main-content" className="min-w-0" tabIndex={-1}>
            {children}
          </main>
        </div>
      </AuthGuard>
    );
  }

  return (
    <AuthGuard>
      <div className="mx-auto flex min-h-screen max-w-[1600px] gap-4 p-4 md:p-6">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col gap-4">
          <TopBar />
          <main id="main-content" className="min-w-0 flex-1" tabIndex={-1}>
            {children}
          </main>
        </div>
        <NotificationCenter />
      </div>
    </AuthGuard>
  );
}
