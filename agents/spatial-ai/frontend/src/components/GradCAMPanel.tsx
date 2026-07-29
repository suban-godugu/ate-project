"use client";

import { useAnalysis } from "@/hooks/useAnalysis";
import { toDataUrl } from "@/utils/format";

export function GradCAMPanel() {
  const { selected } = useAnalysis();
  const src = toDataUrl(selected?.images?.gradcam);

  return (
    <div className="overflow-hidden rounded-lg border border-[var(--line)]">
      <div className="border-b border-[var(--line)] px-3 py-2 text-xs uppercase tracking-[0.12em] text-[var(--muted)]">
        Grad-CAM
      </div>
      <div className="flex aspect-square items-center justify-center bg-ink-950/5 p-2 dark:bg-black/20">
        {src ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={src} alt="Grad-CAM" className="max-h-full max-w-full object-contain" />
        ) : (
          <span className="text-xs text-[var(--muted)]">No image from API</span>
        )}
      </div>
    </div>
  );
}
