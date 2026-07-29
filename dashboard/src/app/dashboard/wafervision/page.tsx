"use client";

import { WaferVisionPageShell } from "@/wafervision/WaferVisionPageShell";
import { WaferVisionDashboard } from "@/wafervision/WaferVisionDashboard";

export default function WaferVisionPage() {
  return (
    <WaferVisionPageShell
      title="WaferVision"
      subtitle="Spatial AI wafer defect analytics"
      searchPlaceholder="Search wafers, lots, defects..."
      primaryActionLabel="Analyze Wafer"
    >
      <div className="dashboard-content">
        <WaferVisionDashboard />
      </div>
    </WaferVisionPageShell>
  );
}
