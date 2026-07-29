import api from './api'
import type {
  DashboardPayload,
  UnifiedRecommendationSummary,
} from '@/types/api'

export async function getDashboard(): Promise<DashboardPayload> {
  const { data } = await api.get<DashboardPayload>('/recommendations/dashboard')
  return data
}

export async function getUnifiedSummary(): Promise<UnifiedRecommendationSummary> {
  const { data } = await api.get<UnifiedRecommendationSummary>(
    '/recommendations/summary',
  )
  return data
}

export async function refreshRecommendations(): Promise<unknown> {
  const { data } = await api.post('/recommendations/refresh')
  return data
}
