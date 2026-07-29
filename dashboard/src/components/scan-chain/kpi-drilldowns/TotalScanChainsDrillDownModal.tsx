"use client";

import {
  TotalScanChainsDrillCard,
  type TotalScanChainsProps,
} from "@/components/scan-chain/kpi-drilldowns/TotalScanChainsDrillCard";
import {
  Dialog,
  DialogBody,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface TotalScanChainsDrillDownModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  data: TotalScanChainsProps;
}

export function TotalScanChainsDrillDownModal({
  open,
  onOpenChange,
  data,
}: TotalScanChainsDrillDownModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-6xl" onClose={() => onOpenChange(false)}>
        <DialogHeader>
          <DialogTitle>Total Scan Chains</DialogTitle>
          <DialogDescription>
            Chain inventory, distribution by dimension, engineering analytics, and breakdown
          </DialogDescription>
        </DialogHeader>
        <DialogBody className="max-h-[calc(92vh-8rem)]">
          <TotalScanChainsDrillCard {...data} />
        </DialogBody>
      </DialogContent>
    </Dialog>
  );
}
