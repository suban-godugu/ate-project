"use client";

import { motion } from "framer-motion";
import {
  Activity,
  AlertTriangle,
  Battery,
  Brain,
  Clock,
  Gauge,
  Link2,
  MapPin,
  Shield,
  Zap,
} from "lucide-react";
import type { KpiCardModel } from "@/types/kpiDrillDown";
import { severityClass, statusLabel } from "@/lib/kpiDrillDown/kpiDrillDownUtils";
import { Sparkline } from "@/components/common/Sparkline";

const ICONS: Record<string, React.ReactNode> = {
  broken_chains: <Link2 size={16} />,
  debug_recommendations: <Brain size={16} />,
  avg_ai_confidence: <Gauge size={16} />,
  constraint_violations: <Shield size={16} />,
  pending_review: <Clock size={16} />,
  coverage_impact: <Activity size={16} />,
  timing_violations: <AlertTriangle size={16} />,
  timing_debug_recs: <Clock size={16} />,
  worst_slack: <Zap size={16} />,
  power_violations: <Battery size={16} />,
  power_debug_recs: <Battery size={16} />,
  peak_switching: <Zap size={16} />,
  defect_suspects: <MapPin size={16} />,
  investigation_recs: <MapPin size={16} />,
  defect_localization: <MapPin size={16} />,
};

export function KpiCardView({
  kpi,
  onClick,
}: {
  kpi: KpiCardModel;
  onClick: () => void;
}) {
  const trend =
    kpi.trendPct === 0
      ? "0%"
      : `${kpi.trendPct > 0 ? "+" : ""}${kpi.trendPct}%`;

  return (
    <motion.button
      type="button"
      whileHover={{ y: -2 }}
      onClick={onClick}
      title={kpi.tooltip}
      className="glass-card gradient-border group relative w-full p-4 text-left"
    >
      <div className="mb-3 flex items-start justify-between gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-primary/15 text-primary">
          {ICONS[kpi.id] ?? <Activity size={16} />}
        </div>
        <span
          className={`rounded-full border px-2 py-0.5 text-[10px] font-medium capitalize ${severityClass(kpi.severity)}`}
        >
          {kpi.severity}
        </span>
      </div>
      <div className="mb-1 text-xs uppercase tracking-wide text-slate-400">{kpi.title}</div>
      <div className="font-display text-3xl font-semibold tracking-tight text-white">
        {kpi.value}
      </div>
      <div className="mt-1 flex items-center justify-between text-xs">
        <span className="text-muted">Target {kpi.target}</span>
        <span className={kpi.trendPct < 0 ? "text-danger" : "text-success"}>{trend}</span>
      </div>
      <div className="mt-1 text-[11px] capitalize text-slate-500">{statusLabel(kpi.status)}</div>
      <div className="mt-3">
        <Sparkline data={kpi.sparkline} />
      </div>
    </motion.button>
  );
}
