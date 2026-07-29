import type { RecommendationCategory } from "@/types/kpiDrillDown";

export const ACTION_LABELS: Record<RecommendationCategory, string> = {
  SCAN_CHAIN_DEBUG: "Inspect Scan Chain",
  TIMING_DEBUG: "Review Capture Clock Timing",
  POWER_RELATED_DEBUG: "Check IR-Drop During Capture",
  ATPG_CONSTRAINT_REVIEW: "Review ATPG Constraints",
  PHYSICAL_DEFECT_INVESTIGATION: "Investigate Physical Defect",
};

export function formatActionLabel(
  category: RecommendationCategory | string,
  chainHint?: string | number
): string {
  const base =
    ACTION_LABELS[category as RecommendationCategory] ??
    String(category).replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  if (chainHint !== undefined && chainHint !== "") {
    return `${base} ${chainHint}`;
  }
  return base;
}
