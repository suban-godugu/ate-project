import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'
import type { EvaluationRunResult } from '../types/evaluation'

interface WorkbenchState {
  executionId: string | null
  setExecutionId: (id: string | null) => void
  lastRun: EvaluationRunResult | null
  setLastRun: (run: EvaluationRunResult | null) => void
  selectedDatasetId: string | null
  setSelectedDatasetId: (id: string | null) => void
  isRunning: boolean
  setIsRunning: (v: boolean) => void
}

const WorkbenchContext = createContext<WorkbenchState | null>(null)

export function WorkbenchProvider({ children }: { children: ReactNode }) {
  const [executionId, setExecutionId] = useState<string | null>(null)
  const [lastRun, setLastRun] = useState<EvaluationRunResult | null>(null)
  const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(null)
  const [isRunning, setIsRunning] = useState(false)

  const value = useMemo(
    () => ({
      executionId,
      setExecutionId,
      lastRun,
      setLastRun,
      selectedDatasetId,
      setSelectedDatasetId,
      isRunning,
      setIsRunning,
    }),
    [executionId, lastRun, selectedDatasetId, isRunning],
  )

  return <WorkbenchContext.Provider value={value}>{children}</WorkbenchContext.Provider>
}

export function useWorkbench() {
  const ctx = useContext(WorkbenchContext)
  if (!ctx) throw new Error('useWorkbench must be used within WorkbenchProvider')
  return ctx
}
