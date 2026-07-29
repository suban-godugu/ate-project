"use client";

import { useCallback, useMemo, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { ScanCoverageDrill } from "@/components/scan-chain/drill/scan-coverage/ScanCoverageDrill";
import { getScanCoverageDrillData } from "@/lib/mock/scanCoverage";

export default function ScanCoverageDrillPage() {
  const [refreshKey, setRefreshKey] = useState(0);

  const data = useMemo(() => getScanCoverageDrillData(), [refreshKey]);

  const handleRefresh = useCallback(() => {
    setRefreshKey((k) => k + 1);
  }, []);

  return (
    <DashboardLayout
      title="Scan Chain Analysis"
      searchPlaceholder="Search scan chains, patterns, chips, flops..."
      primaryActionLabel="AI Diagnose"
      pageId="scan-chain"
      hideQuickFilters
    >
      <div className="p-4 lg:p-6">
        <ScanCoverageDrill data={data} onRefresh={handleRefresh} />
      </div>
    </DashboardLayout>
  );
}
