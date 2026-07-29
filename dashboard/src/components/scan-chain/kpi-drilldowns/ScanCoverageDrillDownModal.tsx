"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ScanCoverageDrill } from "@/components/scan-chain/drill/scan-coverage/ScanCoverageDrill";
import { getScanCoverageDrillData } from "@/lib/mock/scanCoverage";

interface ScanCoverageDrillDownModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ScanCoverageDrillDownModal({ open, onOpenChange }: ScanCoverageDrillDownModalProps) {
  const [refreshKey, setRefreshKey] = useState(0);

  const data = useMemo(() => getScanCoverageDrillData(), [refreshKey]);

  const handleRefresh = useCallback(() => {
    setRefreshKey((k) => k + 1);
  }, []);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onOpenChange(false);
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open, onOpenChange]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <button
        type="button"
        aria-label="Close Scan Coverage analytics workspace overlay"
        className="absolute inset-0 bg-black/80 backdrop-blur-md"
        onClick={() => onOpenChange(false)}
      />
      <div className="relative z-10 h-[90vh] w-[90vw] max-w-[1800px]">
        <ScanCoverageDrill data={data} onRefresh={handleRefresh} onClose={() => onOpenChange(false)} />
      </div>
    </div>
  );
}
