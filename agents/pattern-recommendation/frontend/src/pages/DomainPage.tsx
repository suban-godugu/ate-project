import { useMemo } from 'react'
import { RecommendationTable } from '@/components/RecommendationTable'
import { Badge } from '@/components/Badge'
import { useDashboardStore } from '@/contexts/dashboardStore'
import { postMlFeedback } from '@/services/mlApi'
import type { DomainKey } from '@/types/api'
import {
  DOMAIN_LABELS,
  FEASIBILITY_NOTES,
  PREFERRED_COLUMNS,
  TABLE_KEYS,
} from '@/utils/format'

interface DomainPageProps {
  domain: DomainKey
}

export function DomainPage({ domain }: DomainPageProps) {
  const dashboard = useDashboardStore((s) => s.dashboard)
  const globalSearch = useDashboardStore((s) => s.globalSearch)
  const pushToast = useDashboardStore((s) => s.pushToast)

  const rows = useMemo(() => {
    const tableKey = TABLE_KEYS[domain]
    const tables = dashboard?.tables as Record<string, Record<string, unknown>[]> | undefined
    return tables?.[tableKey] ?? []
  }, [dashboard, domain])

  const columns = useMemo(() => {
    if (!rows.length) return PREFERRED_COLUMNS[domain]
    const preferred = PREFERRED_COLUMNS[domain].filter((c) => c in rows[0])
    const other = Object.keys(rows[0]).filter((c) => !preferred.includes(c))
    return [...preferred, ...other]
  }, [rows, domain])

  const feedbackDomain =
    domain === 'removal' || domain === 'ordering' ? domain : undefined

  const feasibility = dashboard?.feasibility
  const liveNote = (() => {
    if (!feasibility) return FEASIBILITY_NOTES[domain]
    const map: Record<DomainKey, string | undefined> = {
      removal: feasibility.pattern_removal,
      ordering: feasibility.pattern_ordering,
      redundancy: feasibility.redundant_patterns,
      gap: feasibility.additional_atpg,
      low_power: feasibility.low_power_sets,
      coverage: feasibility.coverage_improvement,
    }
    const live = map[domain]
    return live ? `Feasibility: ${live}` : FEASIBILITY_NOTES[domain]
  })()

  if (!dashboard) {
    return (
      <div className="card-surface p-8 text-center text-sm text-ink-400">
        Unified recommendations are unavailable. Start the API and refresh.
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="text-lg font-semibold text-ink-100">
          {DOMAIN_LABELS[domain]}
        </h2>
        <Badge tone="accent">{rows.length} rows</Badge>
        {feedbackDomain ? (
          <Badge tone="neutral">Operator feedback enabled</Badge>
        ) : null}
      </div>
      <div className="rounded-xl border border-accent-600/25 bg-accent-700/10 px-4 py-3 text-sm text-accent-400">
        {liveNote}
      </div>
      <RecommendationTable
        rows={rows}
        columns={columns}
        search={globalSearch}
        exportName={`${domain}_recommendations.csv`}
        feedbackDomain={feedbackDomain}
        onFeedback={
          feedbackDomain
            ? async (patternId, decision) => {
                try {
                  await postMlFeedback({
                    domain: feedbackDomain,
                    pattern_id: patternId,
                    decision,
                  })
                  pushToast(
                    'success',
                    `${decision === 'accept' ? 'Accepted' : 'Rejected'} ${patternId}`,
                  )
                } catch {
                  pushToast('error', `Failed to record feedback for ${patternId}`)
                }
              }
            : undefined
        }
      />
    </div>
  )
}
