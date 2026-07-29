export type CoverageDistributionTab =
  | "Module"
  | "Product"
  | "Pattern"
  | "Vector"
  | "Tester"
  | "Wafer";

export interface CoverageDistributionItem {
  name: string;
  coveragePct: number;
  sharePct: number;
}

export interface CoverageStatusSlice {
  fullyCovered: number;
  partiallyCovered: number;
  uncovered: number;
  /** Total entities used to derive category counts from percentages. */
  entityCount: number;
}

export interface CoverageExecutiveCard {
  id: string;
  label: string;
  value: string;
  icon: string;
  sparkline: number[];
  variant?: "default" | "success" | "warning" | "danger" | "info";
}

export interface CoverageDiagnosisData {
  confidence: number;
  summary: string;
  factors: string[];
}

export interface CoverageMetadataField {
  label: string;
  value: string;
}

export interface CoverageTimelineStep {
  id: string;
  label: string;
  timestamp: string;
  status: "complete" | "running" | "pending" | "failed";
}

export interface CoverageTableColumn {
  key: string;
  label: string;
  defaultVisible?: boolean;
}

export interface CoverageTableRow {
  entityId: string;
  type: string;
  metric: string;
  coverage: string;
  delta: string;
  tester: string;
  severity: string;
}

export interface CoverageRelatedModule {
  id: string;
  label: string;
  route: string;
}

export interface ScanCoverageHeader {
  name: string;
  icon: string;
  currentValue: string;
  statusBadge: string;
  statusVariant: "success" | "warning" | "danger" | "info";
  riskLevel: "critical" | "high" | "medium" | "low" | "nominal";
  trendLabel: string;
  trendDirection: "up" | "down" | "flat";
  lastUpdated: string;
  activeFilters: {
    fab: string;
    tester: string;
    product: string;
    lot: string;
    wafer: string;
  };
}

export interface ScanCoverageDrillData {
  header: ScanCoverageHeader;
  executiveSummary: CoverageExecutiveCard[];
  distributionByTab: Record<CoverageDistributionTab, CoverageDistributionItem[]>;
  status: CoverageStatusSlice;
  diagnosis: CoverageDiagnosisData;
  metadata: CoverageMetadataField[];
  timeline: CoverageTimelineStep[];
  table: {
    columns: CoverageTableColumn[];
    rows: CoverageTableRow[];
  };
  relatedModules: CoverageRelatedModule[];
}
