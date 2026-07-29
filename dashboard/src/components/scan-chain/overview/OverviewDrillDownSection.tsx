"use client";

import { EnterpriseKPIGrid } from "@/components/common/EnterpriseKPICard";
import type { UnifiedKPI } from "@/types/kpi";
import type { ScanChainTab } from "@/types/scanChain";
import { useScanChainNavigation } from "@/components/scan-chain/ScanChainNavigationContext";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

export interface OverviewMiniKPI {
  id: string;
  label: string;
  value: string;
}

function toUnifiedMiniKPI(item: OverviewMiniKPI): UnifiedKPI {
  return {
    id: item.id,
    title: item.label,
    value: item.value,
    change: 0,
    trend: "up",
    sparkline: [0, 0, 0, 0, 0, 0, 0],
    icon: "target",
    positiveIsGood: true,
    status: "ACTIVE",
    statusVariant: "info",
  };
}

export function OverviewMiniKPIGrid({ items }: { items: OverviewMiniKPI[] }) {
  return (
    <EnterpriseKPIGrid
      data={items.map(toUnifiedMiniKPI)}
      variant="overview"
      showSparkline={false}
    />
  );
}

export function OverviewSectionHeader({
  title,
  subtitle,
}: {
  title: string;
  subtitle?: string;
}) {
  return (
    <div className="mb-4 border-l-2 border-[#8B5CF6] pl-3">
      <h2 className="text-base font-bold uppercase tracking-wider text-[#F1F5F9]">
        {title}
      </h2>
      {subtitle && <p className="mt-1.5 text-sm leading-relaxed text-[#94A3B8]">{subtitle}</p>}
    </div>
  );
}

export function OverviewDrillDownSection({
  title,
  subtitle,
  targetTab,
  linkLabel,
  children,
}: {
  title: string;
  subtitle?: string;
  targetTab: ScanChainTab;
  linkLabel: string;
  children: React.ReactNode;
}) {
  const navigate = useScanChainNavigation();

  return (
    <section className="w-full">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <OverviewSectionHeader title={title} subtitle={subtitle} />
        <Button
          variant="ghost"
          size="sm"
          className="h-8 text-xs text-[#7C3AED] hover:bg-[#7C3AED]/10 hover:text-[#A78BFA]"
          onClick={() => navigate(targetTab)}
        >
          {linkLabel}
          <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
        </Button>
      </div>
      {children}
    </section>
  );
}
