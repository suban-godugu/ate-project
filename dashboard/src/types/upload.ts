export type UploadStatus = "Queued" | "Uploading" | "Parsing" | "Processing" | "Completed" | "Failed";

export type DataModule =
  | "Auto Detect"
  | "Scan Chain Analysis"
  | "MBIST Analysis"
  | "LBIST Analysis"
  | "Wafer Analysis"
  | "Cost Intelligence"
  | "Recommendation Analysis";

export type LogModule =
  | "Auto Detect"
  | "Scan Chain"
  | "MBIST"
  | "LBIST"
  | "Wafer Analysis"
  | "Cost Intelligence"
  | "Recommendation Analysis";

export type TesterType = "UltraFlex" | "UltraFLEX Plus" | "V93000" | "J750" | "T2000" | "Other";

export interface UploadMetadata {
  fab: string;
  tester: string;
  product: string;
  lotId: string;
  waferId: string;
  deviceName?: string;
  operator?: string;
  comments?: string;
  notes?: string;
}

export interface DataUploadRecord {
  id: string;
  fileName: string;
  module: string;
  fileType: string;
  size: string;
  uploadedBy: string;
  uploadTime: string;
  status: UploadStatus;
}

export interface LogUploadRecord {
  id: string;
  fileName: string;
  module: string;
  tester: string;
  lotId: string;
  waferId: string;
  fileType: string;
  size: string;
  uploadTime: string;
  status: UploadStatus;
  processingTime: string;
  uploadedBy: string;
}

export interface AILogSummary {
  filesProcessed: string;
  patternsFound: string;
  scanChains: string;
  memoryBlocks: string;
  logicBlocks: string;
  waferCount: string;
  defectsFound: string;
  yield: string;
  estimatedTestCost: string;
  estimatedSavings: string;
}

export interface ValidationResult {
  fileType: string;
  corrupted: boolean;
  unsupported: boolean;
  duplicate: boolean;
  missingMetadata: boolean;
  valid: boolean;
  message: string;
}

export interface UploadProgressState {
  percent: number;
  speed: string;
  elapsed: string;
  remaining: string;
  fileSize: string;
  stageLabel?: string;
  failed?: boolean;
  failedStage?: string;
  errorMessage?: string;
  jobId?: string;
}

export interface PipelineStep {
  id: string;
  label: string;
  status: "pending" | "active" | "done";
}

export type ToastType = "success" | "error" | "info";

export interface UploadToastMessage {
  id: string;
  message: string;
  type: ToastType;
}

export const DATA_FILE_EXTENSIONS = [".stdf", ".stil", ".wgl", ".csv", ".xlsx", ".json", ".zip", ".xml"];
export const LOG_FILE_EXTENSIONS = [".stdf", ".stil", ".wgl", ".log", ".txt", ".csv", ".json", ".xml", ".zip", ".gz"];

export const DATA_MAX_SIZE_GB = 10;
/** Same ceiling as Upload Data / backend MAX_UPLOAD_BYTES (10 GB). */
export const LOG_MAX_SIZE_GB = 10;
