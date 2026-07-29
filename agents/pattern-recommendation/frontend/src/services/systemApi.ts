import api from './api'
import type { HealthResponse } from '@/types/api'

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>('/health')
  return data
}

export async function getVersion(): Promise<{ version: string }> {
  const { data } = await api.get<{ version: string }>('/version')
  return data
}
