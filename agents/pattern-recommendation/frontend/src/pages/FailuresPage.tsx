import { useMemo, useState } from 'react'
import { Download } from 'lucide-react'
import { Badge, severityTone } from '@/components/Badge'
import { StatCard } from '@/components/StatCard'
import { useDashboardStore } from '@/contexts/dashboardStore'
import type { FailurePatternRow } from '@/types/api'
import { downloadCsv, rowsToCsv } from '@/utils/format'

export function FailuresPage() {
  const failure = useDashboardStore((s) => s.failure)
  const globalSearch = useDashboardStore((s) => s.globalSearch)

  const [severityFilter, setSeverityFilter] = useState<string[]>([])
  const [lotFilter, setLotFilter] = useState('')
  const [minFailed, setMinFailed] = useState(0)
  const [showAll, setShowAll] = useState(false)
  const [selectedId, setSelectedId] = useState('')

  const patterns = failure?.patterns ?? []
  const summary = failure?.summary

  const allLots = useMemo(() => {
    const set = new Set<string>()
    for (const p of patterns) {
      for (const lot of p.affected_lots ?? []) set.add(lot)
    }
    return [...set].sort()
  }, [patterns])

  const severities = useMemo(() => {
    return [...new Set(patterns.map((p) => p.severity.toUpperCase()))].sort()
  }, [patterns])

  const activeSeverities = severityFilter.length ? severityFilter : severities

  const filtered = useMemo(() => {
    const q = globalSearch.trim().toLowerCase()
    return patterns
      .filter((p) => {
        if (q && !p.pattern_id.toLowerCase().includes(q)) return false
        if (!activeSeverities.includes(p.severity.toUpperCase())) return false
        if (lotFilter && !(p.affected_lots ?? []).includes(lotFilter)) return false
        if (p.failed_logs < minFailed) return false
        return true
      })
      .sort((a, b) => a.rank - b.rank)
  }, [patterns, globalSearch, activeSeverities, lotFilter, minFailed])

  const visible = showAll ? filtered : filtered.slice(0, 50)
  const selected =
    visible.find((p) => p.pattern_id === selectedId) ?? visible[0] ?? null

  const onExport = () => {
    const rows = visible.map((p) => ({
      rank: p.rank,
      pattern_id: p.pattern_id,
      failed_logs: p.failed_logs,
      coverage_percent: p.coverage_percent,
      severity: p.severity,
      affected_lots: p.affected_lots,
      failing_log_count: p.failing_log_count,
    }))
    downloadCsv(
      'failure_aggregation.csv',
      rowsToCsv(rows, [
        'rank',
        'pattern_id',
        'failed_logs',
        'coverage_percent',
        'severity',
        'affected_lots',
        'failing_log_count',
      ]),
    )
  }

  if (!failure) {
    return (
      <div className="card-surface p-8 text-center text-sm text-ink-400">
        Failure summary is unavailable. Run the aggregation agent or refresh.
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Failed logs" value={summary?.failed_logs ?? 0} />
        <StatCard label="Good logs" value={summary?.good_logs ?? 0} />
        <StatCard
          label="Severity HIGH / MED / LOW"
          value={`${summary?.severity_high ?? 0} / ${summary?.severity_medium ?? 0} / ${summary?.severity_low ?? 0}`}
        />
        <StatCard
          label="Pattern occurrences"
          value={summary?.total_pattern_occurrences ?? 0}
        />
      </div>

      <div className="card-surface grid gap-3 p-4 md:grid-cols-2 xl:grid-cols-5">
        <label className="text-xs text-ink-400">
          Severity
          <select
            multiple
            value={severityFilter}
            onChange={(e) =>
              setSeverityFilter(
                [...e.target.selectedOptions].map((o) => o.value),
              )
            }
            className="mt-1 h-24 w-full rounded-xl border border-white/10 bg-surface-900 px-3 py-2 text-sm text-ink-100"
          >
            {severities.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs text-ink-400">
          Affected lot
          <select
            value={lotFilter}
            onChange={(e) => setLotFilter(e.target.value)}
            className="mt-1 w-full rounded-xl border border-white/10 bg-surface-900 px-3 py-2 text-sm text-ink-100"
          >
            <option value="">All lots</option>
            {allLots.map((lot) => (
              <option key={lot} value={lot}>
                {lot}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs text-ink-400">
          Min failed logs
          <input
            type="number"
            min={0}
            value={minFailed}
            onChange={(e) => setMinFailed(Number(e.target.value) || 0)}
            className="mt-1 w-full rounded-xl border border-white/10 bg-surface-900 px-3 py-2 text-sm text-ink-100"
          />
        </label>
        <label className="flex items-end gap-2 pb-2 text-sm text-ink-300">
          <input
            type="checkbox"
            checked={showAll}
            onChange={(e) => setShowAll(e.target.checked)}
            className="accent-accent-600"
          />
          Show all
        </label>
        <div className="flex items-end">
          <button
            type="button"
            onClick={onExport}
            className="inline-flex w-full items-center justify-center gap-2 rounded-xl border border-white/10 px-3 py-2 text-sm text-ink-200 hover:border-accent-500/40 hover:text-accent-400"
          >
            <Download size={14} /> Export CSV
          </button>
        </div>
      </div>

      <div className="card-surface overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-surface-900/80 text-xs uppercase tracking-wide text-ink-400">
              <tr>
                {[
                  'Rank',
                  'Pattern ID',
                  'Failed Logs',
                  'Coverage %',
                  'Severity',
                  'Affected Lots',
                  'Failing Log Count',
                ].map((h) => (
                  <th key={h} className="px-4 py-3 font-medium">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visible.map((row: FailurePatternRow) => (
                <tr
                  key={row.pattern_id}
                  onClick={() => setSelectedId(row.pattern_id)}
                  className={`cursor-pointer border-t border-white/5 hover:bg-accent-700/10 ${
                    selected?.pattern_id === row.pattern_id
                      ? 'bg-accent-700/15'
                      : ''
                  }`}
                >
                  <td className="px-4 py-2.5 font-mono text-ink-200">{row.rank}</td>
                  <td className="px-4 py-2.5 font-mono text-ink-100">
                    {row.pattern_id}
                  </td>
                  <td className="px-4 py-2.5 font-mono">{row.failed_logs}</td>
                  <td className="px-4 py-2.5 font-mono">
                    {row.coverage_percent.toFixed(2)}
                  </td>
                  <td className="px-4 py-2.5">
                    <Badge tone={severityTone(row.severity)}>{row.severity}</Badge>
                  </td>
                  <td className="max-w-[240px] truncate px-4 py-2.5 text-ink-300">
                    {(row.affected_lots ?? []).join(', ')}
                  </td>
                  <td className="px-4 py-2.5 font-mono">
                    {row.failing_log_count}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="border-t border-white/8 px-4 py-3 text-xs text-ink-400">
          Showing {visible.length} of {filtered.length} matching patterns
          {!showAll && filtered.length > 50 ? ' (top 50)' : ''}
        </p>
      </div>

      <div className="card-surface p-4">
        <h3 className="mb-2 text-sm font-semibold text-ink-100">
          Failing log paths
          {selected ? ` · ${selected.pattern_id}` : ''}
        </h3>
        {selected?.failing_logs?.length ? (
          <pre className="max-h-56 overflow-auto rounded-xl bg-surface-950/70 p-3 font-mono text-xs text-ink-300">
            {selected.failing_logs.join('\n')}
          </pre>
        ) : (
          <p className="text-sm text-ink-400">
            No failing log paths recorded for this pattern.
          </p>
        )}
      </div>
    </div>
  )
}
