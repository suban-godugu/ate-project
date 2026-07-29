import type { ThemeConfig, AccountPreset } from "@/types/theme";
import type { DataUploadRecord, LogUploadRecord, AILogSummary } from "@/types/upload";

export type DatePreset =
  | "today"
  | "yesterday"
  | "7d"
  | "30d"
  | "this-month"
  | "custom";

export interface GlobalFilters {
  datePreset: DatePreset;
  customDateFrom: string;
  customDateTo: string;
  fab: string;
  tester: string;
  product: string;
  lot: string;
  wafer: string;
}

export type SearchCategory =
  | "Dashboard"
  | "Scan Chain"
  | "MBIST"
  | "LBIST"
  | "Wafer"
  | "Cost Intelligence"
  | "Recommendation Analysis"
  | "Alerts";

export interface SearchResultItem {
  id: string;
  title: string;
  subtitle: string;
  category: SearchCategory;
  route: string;
  matchedField: string;
}

export type NotificationSeverity = "critical" | "warning" | "info" | "system";

export interface PlatformNotification {
  id: string;
  title: string;
  message: string;
  severity: NotificationSeverity;
  read: boolean;
  timestamp: string;
  alertRoute?: string;
}

export type RecommendationActionStatus =
  | "pending"
  | "approved"
  | "rejected"
  | "applied";

export interface UserProfile extends AccountPreset {
  avatarInitials: string;
  password: string;
}

export type ExportFormat = "pdf" | "excel" | "csv" | "png";

export type AIDiagnosisStep =
  | "collect"
  | "analyze"
  | "insight"
  | "complete";

export interface AIDiagnosisResult {
  rootCause: string;
  confidence: number;
  recommendation: string;
  estimatedYieldImpact: string;
}

export interface PrimaryActionResult {
  pageId: string;
  label: string;
  summary: string;
  metrics: { label: string; value: string }[];
  completedAt: string;
}

export interface FilterMeta {
  fab: string;
  tester: string;
  product: string;
  lot: string;
  wafer: string;
  dateOffset: number;
}

export interface PersistedUploadState {
  dataHistory: DataUploadRecord[];
  logHistory: LogUploadRecord[];
  lastAILogSummary: AILogSummary;
}

export interface PlatformSettings {
  theme: ThemeConfig;
  account: UserProfile;
}

export const defaultGlobalFilters: GlobalFilters = {
  datePreset: "7d",
  customDateFrom: "",
  customDateTo: "",
  fab: "fab-12",
  tester: "ate-01",
  product: "chip-x7",
  lot: "lot-4421",
  wafer: "wafer-12",
};

export const FILTER_OPTIONS = {
  fab: [
    { value: "fab-12", label: "Fab-12" },
    { value: "fab-18", label: "Fab-18" },
    { value: "all", label: "All Fabs" },
  ],
  tester: [
    { value: "ate-01", label: "ATE-01" },
    { value: "ate-02", label: "ATE-02" },
    { value: "all", label: "All Testers" },
  ],
  product: [
    { value: "chip-x7", label: "Chip-X7" },
    { value: "chip-a3", label: "Chip-A3" },
    { value: "all", label: "All Products" },
  ],
  lot: [
    { value: "lot-4421", label: "LOT-4421" },
    { value: "lot-8832", label: "LOT-8832" },
    { value: "all", label: "All Lots" },
  ],
  wafer: [
    { value: "wafer-12", label: "Wafer-12" },
    { value: "wafer-08", label: "Wafer-08" },
    { value: "all", label: "All Wafers" },
  ],
} as const;
