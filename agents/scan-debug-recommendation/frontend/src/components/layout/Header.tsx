"use client";

export function Header({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <header className="sticky top-0 z-30 flex items-center justify-between border-b border-border/70 bg-[#090B12]/80 px-6 py-4 backdrop-blur-xl">
      <div>
        <div className="text-[10px] uppercase tracking-[0.18em] text-primary">
          COMPTY · Enterprise DFT
        </div>
        <h1 className="font-display text-xl font-semibold text-white">{title}</h1>
        {subtitle ? <p className="text-sm text-muted">{subtitle}</p> : null}
      </div>
      <div className="flex items-center gap-2">
        <span className="rounded-full border border-success/30 bg-success/10 px-3 py-1 text-xs text-success">
          API: {process.env.NEXT_PUBLIC_API_MODE ?? "live"}
        </span>
        <span className="rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs text-primary">
          Agent Online
        </span>
      </div>
    </header>
  );
}
