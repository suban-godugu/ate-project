import { useMemo, useState } from 'react'
import { Check, ChevronLeft, ChevronRight, Download, X } from 'lucide-react'
import { downloadCsv, formatCell, rowsToCsv } from '@/utils/format'

interface RecommendationTableProps {
  rows: Record<string, unknown>[]
  columns: string[]
  search?: string
  pageSize?: number
  exportName: string
  feedbackDomain?: 'removal' | 'ordering'
  onFeedback?: (
    patternId: string,
    decision: 'accept' | 'reject',
  ) => Promise<void> | void
}

export function RecommendationTable({
  rows,
  columns,
  search = '',
  pageSize = 25,
  exportName,
  feedbackDomain,
  onFeedback,
}: RecommendationTableProps) {
  const [page, setPage] = useState(1)
  const [sortKey, setSortKey] = useState<string | null>(null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const [pendingId, setPendingId] = useState<string | null>(null)

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    let next = rows
    if (q) {
      next = rows.filter((row) =>
        columns.some((col) => formatCell(row[col]).toLowerCase().includes(q)),
      )
    }
    if (sortKey) {
      next = [...next].sort((a, b) => {
        const av = a[sortKey]
        const bv = b[sortKey]
        if (typeof av === 'number' && typeof bv === 'number') {
          return sortDir === 'asc' ? av - bv : bv - av
        }
        const as = formatCell(av)
        const bs = formatCell(bv)
        return sortDir === 'asc' ? as.localeCompare(bs) : bs.localeCompare(as)
      })
    }
    return next
  }, [rows, columns, search, sortKey, sortDir])

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize))
  const safePage = Math.min(page, totalPages)
  const start = (safePage - 1) * pageSize
  const pageRows = filtered.slice(start, start + pageSize)

  const onSort = (col: string) => {
    if (sortKey === col) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(col)
      setSortDir('asc')
    }
  }

  const onExport = () => {
    const csv = rowsToCsv(filtered, columns)
    downloadCsv(exportName, csv)
  }

  if (!rows.length) {
    return (
      <div className="card-surface p-8 text-center text-sm text-ink-400">
        No rows for this domain yet.
      </div>
    )
  }

  return (
    <div className="card-surface overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/8 px-4 py-3">
        <p className="text-sm text-ink-300">
          Showing {pageRows.length} of {filtered.length} rows
        </p>
        <button
          type="button"
          onClick={onExport}
          className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-3 py-1.5 text-sm text-ink-200 transition hover:border-accent-500/40 hover:text-accent-400"
        >
          <Download size={14} />
          Export CSV
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-surface-900/80 text-xs uppercase tracking-wide text-ink-400">
            <tr>
              {columns.map((col) => (
                <th key={col} className="px-4 py-3 font-medium whitespace-nowrap">
                  <button
                    type="button"
                    onClick={() => onSort(col)}
                    className="hover:text-accent-400"
                  >
                    {col}
                    {sortKey === col ? (sortDir === 'asc' ? ' ↑' : ' ↓') : ''}
                  </button>
                </th>
              ))}
              {feedbackDomain && onFeedback ? (
                <th className="px-4 py-3 font-medium whitespace-nowrap">Feedback</th>
              ) : null}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row, idx) => {
              const patternId = String(row.pattern_id ?? '')
              return (
              <tr
                key={idx}
                className="border-t border-white/5 transition hover:bg-accent-700/10"
              >
                {columns.map((col) => (
                  <td
                    key={col}
                    className="max-w-[280px] truncate px-4 py-2.5 font-mono text-[13px] text-ink-200"
                    title={formatCell(row[col])}
                  >
                    {formatCell(row[col])}
                  </td>
                ))}
                {feedbackDomain && onFeedback ? (
                  <td className="px-4 py-2.5 whitespace-nowrap">
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        disabled={!patternId || pendingId === patternId}
                        title="Accept"
                        onClick={() => {
                          setPendingId(patternId)
                          void Promise.resolve(onFeedback(patternId, 'accept')).finally(
                            () => setPendingId(null),
                          )
                        }}
                        className="rounded-lg border border-emerald-500/30 p-1.5 text-emerald-300 hover:bg-emerald-500/10 disabled:opacity-40"
                      >
                        <Check size={14} />
                      </button>
                      <button
                        type="button"
                        disabled={!patternId || pendingId === patternId}
                        title="Reject"
                        onClick={() => {
                          setPendingId(patternId)
                          void Promise.resolve(onFeedback(patternId, 'reject')).finally(
                            () => setPendingId(null),
                          )
                        }}
                        className="rounded-lg border border-rose-500/30 p-1.5 text-rose-300 hover:bg-rose-500/10 disabled:opacity-40"
                      >
                        <X size={14} />
                      </button>
                    </div>
                  </td>
                ) : null}
              </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between border-t border-white/8 px-4 py-3">
        <button
          type="button"
          disabled={safePage <= 1}
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-sm text-ink-300 disabled:opacity-40 hover:bg-white/5"
        >
          <ChevronLeft size={16} /> Prev
        </button>
        <span className="text-xs text-ink-400">
          Page {safePage} / {totalPages}
        </span>
        <button
          type="button"
          disabled={safePage >= totalPages}
          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-sm text-ink-300 disabled:opacity-40 hover:bg-white/5"
        >
          Next <ChevronRight size={16} />
        </button>
      </div>
    </div>
  )
}
