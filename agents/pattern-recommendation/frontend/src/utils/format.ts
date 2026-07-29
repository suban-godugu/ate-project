import type { DomainKey } from '@/types/api'

export const DOMAIN_LABELS: Record<DomainKey, string> = {
  removal: 'Removal',
  ordering: 'Ordering',
  redundancy: 'Redundancy',
  gap: 'Gap analysis',
  low_power: 'Low-power',
  coverage: 'Coverage',
}

export const TABLE_KEYS: Record<DomainKey, string> = {
  removal: 'removal_recommendations',
  ordering: 'ordered_patterns',
  redundancy: 'redundant_patterns',
  gap: 'additional_pattern_requests',
  low_power: 'low_activity_pattern_set',
  coverage: 'coverage_gap_recommendations',
}

export const PREFERRED_COLUMNS: Record<DomainKey, string[]> = {
  removal: [
    'pattern_id',
    'removal_priority',
    'confidence',
    'unique_fail_contribution',
    'cluster_id',
    'representative_pattern',
    'reason_codes',
  ],
  ordering: [
    'pattern_id',
    'execution_rank',
    'order_score',
    'fail_rate',
    'severity',
    'mean_toggle_coverage',
    'reason_codes',
  ],
  redundancy: [
    'pattern_id',
    'cluster_id',
    'is_representative',
    'redundant_flag',
    'similarity_to_representative',
    'representative_pattern',
  ],
  gap: [
    'request_id',
    'target_chains',
    'target_lots',
    'suggested_fault_model',
    'rationale',
    'request_only',
  ],
  low_power: [
    'pattern_id',
    'activity_score',
    'toggle_metric',
    'representative',
    'coverage_retained',
    'reason_codes',
  ],
  coverage: [
    'pattern_id',
    'recommendation_type',
    'priority',
    'affected_chains',
    'affected_lots',
    'reason_codes',
  ],
}

export const FEASIBILITY_NOTES: Record<DomainKey, string> = {
  removal: 'Feasibility: full — removal ranking for redundant near-duplicates.',
  ordering: 'Feasibility: full — early failure detection ordering.',
  redundancy: 'Feasibility: full — clustering-based redundancy.',
  gap: 'Feasibility: gap_requests_only — ATPG requests only; no vectors generated.',
  low_power: 'Feasibility: toggle_activity_proxy — not measured power.',
  coverage: 'Feasibility: toggle_fail_proxy — not ATPG fault coverage.',
}

export function formatCell(value: unknown): string {
  if (value == null) return '—'
  if (Array.isArray(value)) return value.map(String).join(', ')
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (typeof value === 'number') {
    return Number.isInteger(value) ? String(value) : value.toFixed(4)
  }
  return String(value)
}

export function rowsToCsv(rows: Record<string, unknown>[], columns: string[]): string {
  const escape = (v: string) => `"${v.replaceAll('"', '""')}"`
  const header = columns.map(escape).join(',')
  const body = rows
    .map((row) => columns.map((col) => escape(formatCell(row[col]))).join(','))
    .join('\n')
  return `${header}\n${body}`
}

export function downloadCsv(filename: string, csv: string): void {
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

export function formatBuiltAt(builtAt?: string | null): string {
  if (!builtAt) return '—'
  if (builtAt.includes('T')) {
    return `${builtAt.replace('T', ' ').split('.')[0]} UTC`
  }
  return builtAt
}
