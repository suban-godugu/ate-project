"use client";

import {
  FailingChainsDrillCard,
  type FailingChainsProps,
} from "@/components/scan-chain/kpi-drilldowns/FailingChainsDrillCard";
import {
  Dialog,
  DialogBody,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface FailingChainsDrillDownModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  data: FailingChainsProps;
}

export function FailingChainsDrillDownModal({
  open,
  onOpenChange,
  data,
}: FailingChainsDrillDownModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-6xl" onClose={() => onOpenChange(false)}>
        <DialogHeader>
          <DialogTitle>Failing Chains</DialogTitle>
          <DialogDescription>
            Failure composition, breakdown by dimension, and operational impact summary
          </DialogDescription>
        </DialogHeader>
        <DialogBody className="max-h-[calc(92vh-8rem)]">
          <FailingChainsDrillCard {...data} />
        </DialogBody>
      </DialogContent>
    </Dialog>
  );
}
