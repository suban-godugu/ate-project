import api from './api'
import type { DatasetStatus } from '@/types/api'

export async function getDatasetsStatus(): Promise<DatasetStatus> {
  const { data } = await api.get<DatasetStatus>('/datasets/status')
  return data
}

export async function refreshDatasets(): Promise<unknown> {
  const { data } = await api.post('/datasets/refresh')
  return data
}
