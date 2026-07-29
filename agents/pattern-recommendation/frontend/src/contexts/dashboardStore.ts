import { create } from 'zustand'
import { getErrorMessage } from '@/services/api'
import { getDatasetsStatus } from '@/services/datasetApi'
import { getFailureSummary, refreshFailures } from '@/services/failureApi'
import { getPatternStatistics } from '@/services/patternApi'
import {
  getDashboard,
  getUnifiedSummary,
  refreshRecommendations,
} from '@/services/recommendationApi'
import { getHealth } from '@/services/systemApi'
import type {
  DashboardPayload,
  DatasetStatus,
  FailureSummaryResponse,
  PatternStatistics,
  UnifiedRecommendationSummary,
} from '@/types/api'

interface ToastItem {
  id: string
  type: 'success' | 'error' | 'info'
  message: string
}

interface DashboardState {
  loading: boolean
  refreshing: boolean
  healthOk: boolean
  datasets: DatasetStatus | null
  failure: FailureSummaryResponse | null
  patternStats: PatternStatistics | null
  dashboard: DashboardPayload | null
  summary: UnifiedRecommendationSummary | null
  errors: string[]
  toasts: ToastItem[]
  globalSearch: string
  loadAll: () => Promise<void>
  refreshAll: () => Promise<void>
  setGlobalSearch: (value: string) => void
  pushToast: (type: ToastItem['type'], message: string) => void
  dismissToast: (id: string) => void
}

export const useDashboardStore = create<DashboardState>((set, get) => ({
  loading: false,
  refreshing: false,
  healthOk: false,
  datasets: null,
  failure: null,
  patternStats: null,
  dashboard: null,
  summary: null,
  errors: [],
  toasts: [],
  globalSearch: '',

  setGlobalSearch: (value) => set({ globalSearch: value }),

  pushToast: (type, message) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
    set((state) => ({ toasts: [...state.toasts, { id, type, message }] }))
    window.setTimeout(() => get().dismissToast(id), 4500)
  },

  dismissToast: (id) =>
    set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),

  loadAll: async () => {
    set({ loading: true, errors: [] })
    const errors: string[] = []

    try {
      const health = await getHealth()
      const healthOk = ['healthy', 'ok', 'operational'].includes(
        String(health.status).toLowerCase(),
      )
      set({ healthOk })
    } catch (error) {
      set({ loading: false, healthOk: false })
      get().pushToast('error', `Backend unavailable: ${getErrorMessage(error)}`)
      throw error
    }

    const [datasets, failure, patternStats, dashboard] = await Promise.all([
      getDatasetsStatus().catch((e) => {
        errors.push(`datasets: ${getErrorMessage(e)}`)
        return null
      }),
      getFailureSummary().catch((e) => {
        errors.push(`failures: ${getErrorMessage(e)}`)
        return null
      }),
      getPatternStatistics().catch((e) => {
        errors.push(`patterns: ${getErrorMessage(e)}`)
        return null
      }),
      getDashboard().catch((e) => {
        errors.push(`dashboard: ${getErrorMessage(e)}`)
        return null
      }),
    ])

    let summary = dashboard?.summary ?? null
    if (!summary) {
      summary = await getUnifiedSummary().catch((e) => {
        errors.push(`summary: ${getErrorMessage(e)}`)
        return null
      })
    }

    set({
      datasets,
      failure,
      patternStats,
      dashboard,
      summary,
      errors,
      loading: false,
    })
  },

  refreshAll: async () => {
    set({ refreshing: true })
    try {
      await refreshFailures()
      await refreshRecommendations()
      await get().loadAll()
      get().pushToast('success', 'Refresh completed')
    } catch (error) {
      get().pushToast('error', getErrorMessage(error))
    } finally {
      set({ refreshing: false })
    }
  },
}))
