"use client";

import { TabLiveShell } from "@/components/platform/TabLiveShell";
import { DonutChart } from "@/components/scan-chain/charts/PieCharts";
import { ChartCard } from "@/components/scan-chain/ChartCard";
import { AgentWorkflowDiagram } from "@/components/recommendation/AgentWorkflowDiagram";
import { BottomSummaryBar } from "@/components/wafer/BottomSummaryBar";
import { DefectClassKPIGrid } from "@/components/wafer/DefectClassKPIGrid";
import { KPIGrid } from "@/components/wafer/KPICard";
import { WaferGalleryGrid } from "@/components/wafer/WaferGalleryGrid";
import { useFilteredWaferData } from "@/hooks/useWaferData";

export function OverviewTab() {
  const liveData = useFilteredWaferData();
  const {bottomSummary,
    defectClassificationKPIs,
    galleryCards,
    inputDieStatsKPIs,
    uploadWorkflowSteps,
  } = liveData;

  const yieldGaugeData = [
    { name: "Positive Yield", value: 93.8, color: "#22C55E" },
    { name: "Negative Yield", value: 6.2, color: "#EF4444" },
  ];

  return (
    <TabLiveShell module="wafer-analysis" hookResult={liveData}>
      <div className="dashboard-content space-y-8">
      <section>
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400">
          Input &amp; Die Statistics
        </h2>
        <KPIGrid data={inputDieStatsKPIs} />
      </section>

      <section>
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400">
          Defect Classification
        </h2>
        <DefectClassKPIGrid data={defectClassificationKPIs} />
      </section>

      <section>
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400">
          Yield Analysis
        </h2>
        <ChartCard title="Positive / Negative Yield" subtitle="Current lot yield split" className="max-w-md">
          <DonutChart data={yieldGaugeData} centerLabel="Net Yield" centerValue="93.8%" />
        </ChartCard>
      </section>

      <section>
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400">
          Wafer Defect Classification Gallery
        </h2>
        <WaferGalleryGrid cards={galleryCards} />
      </section>

      <AgentWorkflowDiagram
        steps={uploadWorkflowSteps}
        title="Upload Workflow"
        subtitle="End-to-end wafer image analysis pipeline"
      />

      <section>
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400">
          Summary
        </h2>
        <BottomSummaryBar data={bottomSummary} />
      </section>
      </div>
    </TabLiveShell>
  );
}
