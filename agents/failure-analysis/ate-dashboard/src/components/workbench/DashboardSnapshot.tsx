"use client";

import { memo, useState } from "react";
import { Camera } from "lucide-react";
import { notify } from "@/stores/toastStore";

type Props = { targetId?: string };

export const DashboardSnapshot = memo(function DashboardSnapshot({
  targetId = "workbench-root",
}: Props) {
  const [busy, setBusy] = useState(false);

  async function capture() {
    setBusy(true);
    try {
      const el = document.getElementById(targetId);
      if (!el) throw new Error("Dashboard root not found");
      const { default: html2canvas } = await import("html2canvas");
      const canvas = await html2canvas(el, {
        backgroundColor: "#090b12",
        scale: 2,
        useCORS: true,
      });
      const link = document.createElement("a");
      link.download = `fa-dashboard-${Date.now()}.png`;
      link.href = canvas.toDataURL("image/png");
      link.click();
      notify({ title: "Snapshot Saved", description: "PNG downloaded.", variant: "success" });
    } catch (err) {
      notify({
        title: "Snapshot Failed",
        description: err instanceof Error ? err.message : "Could not capture dashboard",
        variant: "error",
      });
    } finally {
      setBusy(false);
    }
  }

  return (
    <button
      type="button"
      onClick={capture}
      disabled={busy}
      data-testid="dashboard-snapshot"
      className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm hover:bg-white/10 disabled:opacity-50"
    >
      <Camera size={16} />
      {busy ? "Capturing…" : "Download PNG Snapshot"}
    </button>
  );
});
