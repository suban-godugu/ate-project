"use client";

import { TabLiveShell } from "@/components/platform/TabLiveShell";
import { useEffect, useMemo, useState } from "react";
import { AgentWorkflowDiagram } from "@/components/recommendation/AgentWorkflowDiagram";
import { KPIGrid } from "@/components/wafer/KPICard";
import { UploadHistoryPanel } from "@/components/wafer/UploadHistoryPanel";
import { WaferAnalysisViews } from "@/components/wafer/WaferAnalysisViews";
import { WaferInfoPanel } from "@/components/wafer/WaferInfoPanel";
import { useFilteredWaferData } from "@/hooks/useWaferData";
import type { WaferDefectClass, WaferUploadHistoryItem } from "@/types/wafer";

export function DefectClassTab({ defectClass }: { defectClass: WaferDefectClass }) {
  const liveData = useFilteredWaferData();
  const {getDefectBundle, uploadWorkflowSteps } = liveData;
  const bundle = useMemo(() => getDefectBundle(defectClass), [getDefectBundle, defectClass]);
  const { meta, kpis, allUploads, infoPanel } = bundle;
  const [selectedUpload, setSelectedUpload] = useState<WaferUploadHistoryItem>(allUploads[0]!);

  useEffect(() => {
    setSelectedUpload(allUploads[0]!);
  }, [defectClass, allUploads]);

  const panelData = useMemo(
    () => ({
      ...infoPanel,
      assignedLot: selectedUpload.lot,
      confidence: selectedUpload.confidence,
    }),
    [infoPanel, selectedUpload]
  );

  return (
    <TabLiveShell module="wafer-analysis" tab={defectClass} hookResult={liveData}>
      <div className="dashboard-content space-y-8">
      <div className="glass-card gradient-border p-6">
        <h2 className="text-xl font-bold text-white">{meta.label} Defect Analysis</h2>
        <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-400">{meta.description}</p>
      </div>

      <KPIGrid data={kpis} />

      <UploadHistoryPanel
        items={allUploads}
        selectedId={selectedUpload.id}
        onSelect={setSelectedUpload}
      />

      <WaferAnalysisViews classId={defectClass} upload={selectedUpload} />

      <WaferInfoPanel data={panelData} />

      <AgentWorkflowDiagram
        steps={uploadWorkflowSteps}
        title="Analysis Workflow"
        subtitle="Wafer upload to saved analysis pipeline"
      />
      </div>
    </TabLiveShell>
  );
}
