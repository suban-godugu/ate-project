import api from './api'
import type { FailureSummaryResponse } from '@/types/api'

export async function getFailureSummary(): Promise<FailureSummaryResponse> {
  const { data } = await api.get<FailureSummaryResponse>('/failures/summary')
  return data
}

export async function refreshFailures(): Promise<FailureSummaryResponse> {
  const { data } = await api.post<FailureSummaryResponse>('/failures/refresh')
  return data
}
