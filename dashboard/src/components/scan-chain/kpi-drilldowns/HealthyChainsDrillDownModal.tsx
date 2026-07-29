"use client";

import {
  HealthyChainsDrillCard,
  type HealthyChainsProps,
} from "@/components/scan-chain/kpi-drilldowns/HealthyChainsDrillCard";
import {
  Dialog,
  DialogBody,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface HealthyChainsDrillDownModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  data: HealthyChainsProps;
}

export function HealthyChainsDrillDownModal({
  open,
  onOpenChange,
  data,
}: HealthyChainsDrillDownModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-6xl" onClose={() => onOpenChange(false)}>
        <DialogHeader>
          <DialogTitle>Healthy Chains</DialogTitle>
          <DialogDescription>
            Healthy chain distribution, status mix, breakdown analysis, and health diagnosis
          </DialogDescription>
        </DialogHeader>
        <DialogBody className="max-h-[calc(92vh-8rem)]">
          <HealthyChainsDrillCard {...data} />
        </DialogBody>
      </DialogContent>
    </Dialog>
  );
}
