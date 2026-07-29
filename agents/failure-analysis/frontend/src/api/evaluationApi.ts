import api from './client'
import type {
  DashboardPayload,
  DatasetInventory,
  EvaluationRunResult,
  EvaluationRunSummary,
  ImprovementRecommendation,
  LogEntry,
  WorkbenchOverview,
} from '../types/evaluation'

export async function discoverDatasets(): Promise<DatasetInventory> {
  const { data } = await api.get<DatasetInventory>('/evaluation/datasets')
  return data
}

export async function listEvaluationRuns(limit = 50): Promise<{ runs: EvaluationRunSummary[] }> {
  const { data } = await api.get<{ runs: EvaluationRunSummary[] }>(`/evaluation?limit=${limit}`)
  return data
}

export async function runEvaluation(body: {
  dataset_id?: string | null
  modules?: string[] | null
  max_logs?: number | null
}): Promise<EvaluationRunResult> {
  const { data } = await api.post<EvaluationRunResult>('/evaluation/run', body)
  return data
}

export async function getEvaluationDashboard(executionId?: string): Promise<{
  execution_id: string
  dashboard: DashboardPayload
  pass_fail_summary: Record<string, number>
  model_version: string
}> {
  const params = executionId ? `?execution_id=${executionId}` : ''
  const { data } = await api.get(`/evaluation/dashboard${params}`)
  return data
}

export async function getEvaluationReport(executionId?: string): Promise<{
  execution_id: string
  report: EvaluationRunResult
  export_paths: Record<string, string | null>
}> {
  const params = executionId ? `?execution_id=${executionId}` : ''
  const { data } = await api.get(`/evaluation/report${params}`)
  return data
}

export function exportDownloadUrl(fmt: string, executionId: string): string {
  return `/api/v1/evaluation/download/${fmt}?execution_id=${executionId}`
}

export async function getWorkbenchOverview(): Promise<WorkbenchOverview> {
  const { data } = await api.get<WorkbenchOverview>('/workbench/overview')
  return data
}

export async function getImprovements(executionId?: string): Promise<{
  execution_id: string
  recommendations: ImprovementRecommendation[]
  production_readiness: WorkbenchOverview['production_readiness']
  ai_health_score: WorkbenchOverview['ai_health_score']
}> {
  const params = executionId ? `?execution_id=${executionId}` : ''
  const { data } = await api.get(`/workbench/improvements${params}`)
  return data
}

export async function getWorkbenchLogs(
  executionId?: string,
  filters?: { module?: string; status?: string },
): Promise<{ execution_id: string; logs: LogEntry[]; total: number }> {
  const q = new URLSearchParams()
  if (executionId) q.set('execution_id', executionId)
  if (filters?.module) q.set('module', filters.module)
  if (filters?.status) q.set('status', filters.status)
  const { data } = await api.get(`/workbench/logs?${q}`)
  return data
}

export async function getWorkbenchHealth(): Promise<Record<string, unknown>> {
  const { data } = await api.get('/workbench/health')
  return data
}

export async function getWorkbenchVisualizations(executionId?: string): Promise<{
  execution_id: string
  visualizations: {
    charts: Record<string, { type: string; x: string[]; y: number[] }>
    ai_metrics: unknown[]
    benchmark_stages: unknown[]
    confusion_matrix?: { labels: string[]; matrix: number[][] }
    root_cause_predictions?: Record<string, unknown>
    pattern_frequency?: unknown[]
  }
}> {
  const params = executionId ? `?execution_id=${executionId}` : ''
  const { data } = await api.get(`/workbench/visualizations${params}`)
  return data
}

export async function getRootCauseHistory(): Promise<Record<string, unknown>> {
  const { data } = await api.get('/root-cause/history')
  return data
}

export async function getRootCauseRecommendations(): Promise<Record<string, unknown>> {
  const { data } = await api.get('/root-cause/recommendations')
  return data
}
