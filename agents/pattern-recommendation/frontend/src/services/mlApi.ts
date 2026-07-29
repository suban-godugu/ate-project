import api from './api'

export interface MlStatusData {
  ml_enabled: boolean
  ml_shadow_mode: boolean
  removal_model_loaded: boolean
  ordering_model_loaded: boolean
  removal_blend: number
  ordering_blend: number
  artifacts_dir: string
  load_error: string | null
  removal_meta?: { trained_at?: string; best_iteration?: number }
  ordering_meta?: { trained_at?: string; best_iteration?: number }
}

export async function getMlStatus(): Promise<MlStatusData> {
  const { data } = await api.get<{ success: boolean; data: MlStatusData }>('/ml/status')
  return data.data
}

export async function postMlFeedback(payload: {
  domain: 'removal' | 'ordering'
  pattern_id: string
  decision: 'accept' | 'reject' | 'edit'
  note?: string
  metadata?: Record<string, unknown>
}): Promise<unknown> {
  const { data } = await api.post('/ml/feedback', payload)
  return data
}
