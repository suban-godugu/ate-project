"use client";

import { OverallScanHealthDrillCard, type OverallScanHealthProps } from "@/components/scan-chain/kpi-drilldowns/OverallScanHealthDrillCard";
import { Dialog, DialogBody, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";

interface OverallScanHealthDrillDownModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  data: OverallScanHealthProps;
}

export function OverallScanHealthDrillDownModal({
  open,
  onOpenChange,
  data,
}: OverallScanHealthDrillDownModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="max-w-5xl"
        onClose={() => onOpenChange(false)}
      >
        <DialogHeader>
          <DialogTitle>Overall Scan Health</DialogTitle>
          <DialogDescription>
            Executive health score, weighted breakdown, and chain status distribution
          </DialogDescription>
        </DialogHeader>
        <DialogBody className="max-h-[calc(92vh-8rem)]">
          <OverallScanHealthDrillCard {...data} />
        </DialogBody>
      </DialogContent>
    </Dialog>
  );
}
