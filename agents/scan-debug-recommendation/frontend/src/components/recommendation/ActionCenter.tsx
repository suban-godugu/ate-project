"use client";

export function ActionCenter({
  onAction,
}: {
  onAction: (action: string) => void;
}) {
  const actions = [
    "Approve",
    "Reject",
    "Modify",
    "Assign",
    "Generate ATPG Script",
    "Download Report",
    "Export CSV",
  ];
  return (
    <section className="glass-card gradient-border p-4">
      <div className="mb-3">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Action Center</div>
        <h2 className="font-display text-lg font-semibold text-white">Engineer Controls</h2>
      </div>
      <div className="flex flex-wrap gap-2">
        {actions.map((a) => (
          <button
            key={a}
            type="button"
            onClick={() => onAction(a)}
            className="rounded-xl border border-border/80 bg-primary/15 px-3 py-2 text-sm text-white hover:border-primary/50 hover:bg-primary/25"
          >
            {a}
          </button>
        ))}
      </div>
    </section>
  );
}
