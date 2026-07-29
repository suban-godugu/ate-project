"use client";

import { useRouter } from "next/navigation";
import type { CoverageRelatedModule } from "@/types/scanCoverage";

export function RelatedModules({ modules }: { modules: CoverageRelatedModule[] }) {
  const router = useRouter();

  return (
    <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
      {modules.map((mod) => (
        <button
          key={mod.id}
          type="button"
          suppressHydrationWarning
          onClick={() => router.push(mod.route)}
          className="flex items-center justify-between rounded-xl border border-[#2D3748]/60 bg-[#121826]/60 p-3 text-left transition hover:border-[rgba(139,92,246,0.45)] hover:bg-[#8B5CF6]/5"
        >
          <span className="text-sm font-semibold text-white">{mod.label}</span>
        </button>
      ))}
    </div>
  );
}
