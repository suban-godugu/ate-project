export interface HealthResponse {
  status: string
}

export interface DatasetStatus {
  available: number
  missing: number
  invalid: number
  total: number
}

export interface PatternStatistics {
  patterns: number
  total_executions: number
  failed_patterns: number
  average_fail_rate: number
  average_toggle_density: number
}

export interface UnifiedRecommendationSummary {
  patterns_analyzed: number
  clusters: number
  removal_candidates: number
  ordering_candidates: number
  gap_requests: number
  low_power_patterns: number
  coverage_recommendations: number
}

export interface RecommendationFeasibility {
  redundant_patterns: string
  pattern_removal: string
  pattern_ordering: string
  additional_atpg: string
  low_power_sets: string
  coverage_improvement: string
}

export interface DashboardTables {
  redundant_patterns: Record<string, unknown>[]
  removal_recommendations: Record<string, unknown>[]
  ordered_patterns: Record<string, unknown>[]
  additional_pattern_requests: Record<string, unknown>[]
  low_activity_pattern_set: Record<string, unknown>[]
  coverage_gap_recommendations: Record<string, unknown>[]
}

export interface DashboardPayload {
  summary: UnifiedRecommendationSummary
  feasibility: RecommendationFeasibility
  tables: DashboardTables
  artifacts?: Record<string, string>
  built_at?: string | null
}

export interface FailureSummaryStats {
  total_logs: number
  failed_logs: number
  good_logs: number
  unique_patterns: number
  total_pattern_occurrences: number
  total_lots: number
  severity_high: number
  severity_medium: number
  severity_low: number
}

export interface FailurePatternRow {
  rank: number
  pattern_id: string
  failed_logs: number
  coverage_percent: number
  severity: string
  affected_lots: string[]
  failing_logs: string[]
  failing_log_count: number
}

export interface FailureSummaryResponse {
  success: boolean
  message: string
  summary: FailureSummaryStats
  patterns: FailurePatternRow[]
  total_patterns: number
}

export type DomainKey =
  | 'removal'
  | 'ordering'
  | 'redundancy'
  | 'gap'
  | 'low_power'
  | 'coverage'
