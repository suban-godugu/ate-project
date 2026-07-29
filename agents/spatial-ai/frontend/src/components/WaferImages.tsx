"use client";

import { DensityMapPanel } from "@/components/DensityMapPanel";
import { GradCAMPanel } from "@/components/GradCAMPanel";
import { useAnalysis } from "@/hooks/useAnalysis";
import { toDataUrl } from "@/utils/format";

function ImageTile({ title, base64 }: { title: string; base64?: string }) {
  const src = toDataUrl(base64);
  return (
    <div className="overflow-hidden rounded-lg border border-[var(--line)]">
      <div className="border-b border-[var(--line)] px-3 py-2 text-xs uppercase tracking-[0.12em] text-[var(--muted)]">
        {title}
      </div>
      <div className="flex aspect-square items-center justify-center bg-ink-950/5 p-2 dark:bg-black/20">
        {src ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={src} alt={title} className="max-h-full max-w-full object-contain" />
        ) : (
          <span className="text-xs text-[var(--muted)]">No image from API</span>
        )}
      </div>
    </div>
  );
}

export function WaferImages() {
  const { selected } = useAnalysis();
  const images = selected?.images;

  return (
    <section className="panel p-5">
      <h2 className="panel-title mb-4">Image Panels</h2>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <ImageTile title="Original Wafer" base64={images?.original} />
        <ImageTile title="Overlay" base64={images?.overlay} />
        <DensityMapPanel />
        <GradCAMPanel />
      </div>
    </section>
  );
}
