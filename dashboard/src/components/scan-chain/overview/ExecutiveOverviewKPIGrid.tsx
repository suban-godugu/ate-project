"use client";

import { useMemo, useState } from "react";
import { ExecutiveKPICard } from "@/components/common/ExecutiveKPICard";
import { ExecutiveKPIDrillDownModal } from "@/components/common/ExecutiveKPIDrillDownModal";
import { FailingChainsDrillDownModal } from "@/components/scan-chain/kpi-drilldowns/FailingChainsDrillDownModal";
import { HealthyChainsDrillDownModal } from "@/components/scan-chain/kpi-drilldowns/HealthyChainsDrillDownModal";
import { OverallScanHealthDrillDownModal } from "@/components/scan-chain/kpi-drilldowns/OverallScanHealthDrillDownModal";
import { ScanCoverageDrillDownModal } from "@/components/scan-chain/kpi-drilldowns/ScanCoverageDrillDownModal";
import { TotalScanChainsDrillDownModal } from "@/components/scan-chain/kpi-drilldowns/TotalScanChainsDrillDownModal";
import { buildFailingChainsDrillProps } from "@/lib/scan-chain/failingChainsDrillData";
import { buildHealthyChainsDrillProps } from "@/lib/scan-chain/healthyChainsDrillData";
import { buildOverallScanHealthDrillProps } from "@/lib/scan-chain/overallScanHealthDrillData";
import { buildTotalScanChainsDrillProps } from "@/lib/scan-chain/totalScanChainsDrillData";
import type { ScanKPI } from "@/types/scanChain";

const OVERALL_SCAN_HEALTH_ID = "overall-health";
const TOTAL_SCAN_CHAINS_ID = "total-chains";
const HEALTHY_CHAINS_ID = "healthy-chains";
const FAILING_CHAINS_ID = "failing-chains";
const SCAN_COVERAGE_ID = "scan-coverage";

export function ExecutiveOverviewKPIGrid({ data }: { data: ScanKPI[] }) {
  const [selected, setSelected] = useState<ScanKPI | null>(null);
  const [scanCoverageOpen, setScanCoverageOpen] = useState(false);
  const overallScanHealthData = useMemo(() => buildOverallScanHealthDrillProps(), []);
  const totalScanChainsData = useMemo(() => buildTotalScanChainsDrillProps(), []);
  const healthyChainsData = useMemo(() => buildHealthyChainsDrillProps(), []);
  const failingChainsData = useMemo(() => buildFailingChainsDrillProps(), []);

  const closeModal = (open: boolean) => {
    if (!open) setSelected(null);
  };

  return (
    <>
      <div className="kpi-grid-section w-full">
        {data.map((kpi, index) => (
          <ExecutiveKPICard
            key={kpi.id}
            id={kpi.id}
            icon={kpi.icon}
            title={kpi.title}
            value={kpi.value}
            subtitle={kpi.subtitle}
            change={kpi.change}
            positiveIsGood={kpi.positiveIsGood}
            sparkline={kpi.sparkline}
            index={index}
            onClick={() => {
              if (kpi.id === SCAN_COVERAGE_ID) {
                setScanCoverageOpen(true);
                return;
              }
              setSelected(kpi);
            }}
          />
        ))}
      </div>

      {selected?.id === OVERALL_SCAN_HEALTH_ID ? (
        <OverallScanHealthDrillDownModal
          open={Boolean(selected)}
          onOpenChange={closeModal}
          data={overallScanHealthData}
        />
      ) : selected?.id === TOTAL_SCAN_CHAINS_ID ? (
        <TotalScanChainsDrillDownModal
          open={Boolean(selected)}
          onOpenChange={closeModal}
          data={totalScanChainsData}
        />
      ) : selected?.id === HEALTHY_CHAINS_ID ? (
        <HealthyChainsDrillDownModal
          open={Boolean(selected)}
          onOpenChange={closeModal}
          data={healthyChainsData}
        />
      ) : selected?.id === FAILING_CHAINS_ID ? (
        <FailingChainsDrillDownModal
          open={Boolean(selected)}
          onOpenChange={closeModal}
          data={failingChainsData}
        />
      ) : (
        <ExecutiveKPIDrillDownModal
          kpi={selected}
          open={Boolean(selected)}
          onOpenChange={closeModal}
        />
      )}

      <ScanCoverageDrillDownModal open={scanCoverageOpen} onOpenChange={setScanCoverageOpen} />
    </>
  );
}
