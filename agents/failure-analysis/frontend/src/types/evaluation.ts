export type ValidationStatus = 'PASS' | 'FAIL' | 'WARNING' | 'SKIPPED'

export interface DatasetBundle {
  dataset_id: string
  scale_token: string
  stil_paths: string[]
  log_count: number
  labelled_log_count: number
  tabular_paths: string[]
  warnings: string[]
  metadata?: Record<string, unknown>
}

export interface DatasetInventory {
  roots: string[]
  stil_count: number
  log_count: number
  tabular_count: number
  bundles: DatasetBundle[]
  warnings: string[]
  stil_files?: string[]
}

export interface ValidationRow {
  module: string
  status: ValidationStatus
  explanation: string
  duration_ms: number
  dataset_id?: string
}

export interface AIMetrics {
  dataset_id?: string
  scale?: string
  accuracy?: number
  precision?: number
  recall?: number
  f1_score?: number
  roc_auc?: number | null
  engineering_score?: number
  prediction_confidence?: number
  similarity_accuracy?: number
  recommendation_accuracy?: number
  confusion_matrix?: { labels: string[]; matrix: number[][] }
}

export interface BenchmarkStage {
  name: string
  avg_ms: number
  max_ms?: number
  min_ms?: number
  meets_target?: boolean
  cpu_percent?: number | null
  memory_mb?: number | null
  dataset_id?: string
}

export interface EvaluationRunSummary {
  execution_id: string
  datasets_evaluated: number
  pass_count: number
  fail_count: number
  warning_count: number
  model_version: string
  processing_ms: number
  created_at: string | null
}

export interface EvaluationRunResult {
  execution_id: string
  processing_ms: number
  datasets_evaluated: number
  pass_fail_summary: Record<string, number>
  inventory: DatasetInventory
  dataset_results: DatasetResult[]
  latest_training?: TrainingResult
  dashboard?: DashboardPayload
  export_paths?: Record<string, string | null>
}

export interface DatasetResult {
  dataset: DatasetBundle
  logs_evaluated: number
  module_outputs: Record<string, Record<string, unknown>>
  validation: ValidationRow[]
  warnings: string[]
  ai_evaluation: AIMetrics
  training: TrainingResult
  benchmark: { stages: BenchmarkStage[]; total_measured_ms?: number }
  execution_logs: LogEntry[]
}

export interface TrainingResult {
  trained: boolean
  reason?: string
  model_name?: string
  model_version?: string
  validation_accuracy?: number
  sample_count?: number
  comparisons?: { model: string; validation_accuracy?: number; test_accuracy?: number; error?: string }[]
}

export interface DashboardPayload {
  summary_cards: { label: string; value: string | number }[]
  dataset_inventory: DatasetBundle[]
  validation_status: ValidationRow[]
  execution_progress: { module: string; status: string; dataset_id?: string }[]
  ai_metrics: AIMetrics[]
  benchmark_stages: BenchmarkStage[]
  model_performance: unknown[]
  training_status: TrainingResult
  pass_fail_summary: Record<string, number>
  charts: Record<string, { type: string; x: string[]; y: number[] }>
}

export interface WorkbenchOverview {
  total_datasets: number
  stil_count: number
  log_count: number
  tabular_count: number
  current_dataset: string | null
  agent_status: string
  ai_health_score: { score: number; rating: string; factors: Record<string, number> }
  overall_accuracy: number
  overall_confidence: number
  production_readiness: {
    production_ready: boolean
    blockers: string[]
    pass_count: number
    fail_count: number
    warning_count: number
  }
  latest_execution: {
    execution_id: string | null
    processing_ms: number | null
    pass_count: number
    fail_count: number
    warning_count: number
    model_version: string
    created_at: string | null
  }
  system_metrics: {
    cpu_percent: number | null
    memory_mb: number | null
    memory_percent: number | null
    disk_usage_percent: number | null
  }
  database_health: string
  inventory_warnings: string[]
}

export interface ImprovementRecommendation {
  priority: 'High' | 'Medium' | 'Low'
  category: string
  module: string
  dataset_id: string
  recommendation: string
  rationale: string
}

export interface LogEntry {
  execution_id?: string
  correlation_id?: string
  dataset_name?: string
  timestamp: string
  module: string
  status: string
  duration_ms?: number
  message?: string
  exception?: string | null
}

export const FA_MODULES = [
  'FA-FR-001',
  'FA-FR-002',
  'FA-FR-003',
  'FA-FR-004',
  'FA-FR-005',
  'FA-FR-006',
  'FA-FR-007',
  'FA-FR-008',
  'FA-FR-009',
  'FA-FR-010',
] as const

export const MODULE_LABELS: Record<string, string> = {
  'FA-FR-001': 'STIL & Log Ingestion',
  'FA-FR-002': 'Pattern Detection',
  'FA-FR-003': 'Failure Rate Analytics',
  'FA-FR-004': 'Fault Classification',
  'FA-FR-005': 'Recurring Failure Detection',
  'FA-FR-006': 'Pattern Correlation',
  'FA-FR-007': 'Die-Level Analytics',
  'FA-FR-008': 'Wafer-Level Analytics',
  'FA-FR-009': 'Root Cause Prediction',
  'FA-FR-010': 'Engineering Reporting',
}
