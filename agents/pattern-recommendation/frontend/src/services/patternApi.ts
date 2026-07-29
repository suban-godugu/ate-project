import api from './api'
import type { PatternStatistics } from '@/types/api'

export async function getPatternStatistics(): Promise<PatternStatistics> {
  const { data } = await api.get<PatternStatistics>('/patterns/statistics')
  return data
}
