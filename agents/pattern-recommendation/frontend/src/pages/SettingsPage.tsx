import { useEffect, useState } from 'react'
import { RefreshCw } from 'lucide-react'
import { StatCard } from '@/components/StatCard'
import { Badge } from '@/components/Badge'
import { useDashboardStore } from '@/contexts/dashboardStore'
import { formatBuiltAt } from '@/utils/format'
import { refreshDatasets } from '@/services/datasetApi'
import { getMlStatus, type MlStatusData } from '@/services/mlApi'

export function SettingsPage() {
  const datasets = useDashboardStore((s) => s.datasets)
  const healthOk = useDashboardStore((s) => s.healthOk)
  const dashboard = useDashboardStore((s) => s.dashboard)
  const refreshing = useDashboardStore((s) => s.refreshing)
  const refreshAll = useDashboardStore((s) => s.refreshAll)
  const loadAll = useDashboardStore((s) => s.loadAll)
  const pushToast = useDashboardStore((s) => s.pushToast)
  const [mlStatus, setMlStatus] = useState<MlStatusData | null>(null)

  useEffect(() => {
    void getMlStatus()
      .then(setMlStatus)
      .catch(() => setMlStatus(null))
  }, [])

  const onRescan = async () => {
    try {
      await refreshDatasets()
      await loadAll()
      pushToast('success', 'Dataset registry refreshed')
    } catch {
      pushToast('error', 'Failed to refresh datasets')
    }
  }

  return (
    <div className="space-y-5">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="API status"
          value={healthOk ? 'healthy' : 'down'}
        />
        <StatCard label="Available datasets" value={datasets?.available ?? '—'} />
        <StatCard label="Missing datasets" value={datasets?.missing ?? '—'} />
        <StatCard label="Invalid datasets" value={datasets?.invalid ?? '—'} />
      </div>

      <div className="card-surface space-y-4 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-base font-semibold text-ink-100">Operations</h3>
            <p className="text-sm text-ink-400">
              Uses existing FastAPI refresh endpoints only.
            </p>
          </div>
          <Badge tone={healthOk ? 'success' : 'danger'}>
            {healthOk ? 'Connected' : 'Disconnected'}
          </Badge>
        </div>

        <dl className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-xl bg-surface-900/70 p-3">
            <dt className="text-xs uppercase tracking-wide text-ink-400">
              Last built
            </dt>
            <dd className="mt-1 font-mono text-sm text-ink-100">
              {formatBuiltAt(dashboard?.built_at)}
            </dd>
          </div>
          <div className="rounded-xl bg-surface-900/70 p-3">
            <dt className="text-xs uppercase tracking-wide text-ink-400">
              Total datasets
            </dt>
            <dd className="mt-1 font-mono text-sm text-ink-100">
              {datasets?.total ?? '—'}
            </dd>
          </div>
        </dl>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={refreshing}
            onClick={() => void refreshAll()}
            className="inline-flex items-center gap-2 rounded-xl bg-accent-600 px-4 py-2 text-sm font-medium text-white hover:bg-accent-700 disabled:opacity-60"
          >
            <RefreshCw size={15} className={refreshing ? 'animate-spin' : ''} />
            Refresh All
          </button>
          <button
            type="button"
            onClick={() => void onRescan()}
            className="rounded-xl border border-white/10 px-4 py-2 text-sm text-ink-200 hover:bg-white/5"
          >
            Rescan datasets
          </button>
        </div>
      </div>

      <div className="card-surface space-y-3 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-base font-semibold text-ink-100">ML models</h3>
            <p className="text-sm text-ink-400">
              Removal classifier + ordering ranker status (shadow by default).
            </p>
          </div>
          <Badge tone={mlStatus?.removal_model_loaded ? 'success' : 'warning'}>
            {mlStatus?.removal_model_loaded ? 'Artifacts loaded' : 'Not loaded'}
          </Badge>
        </div>
        <pre className="overflow-auto rounded-xl bg-surface-950/70 p-3 font-mono text-xs text-ink-300">
          {JSON.stringify(mlStatus ?? { message: 'ML status unavailable' }, null, 2)}
        </pre>
      </div>

      <div className="card-surface p-5">
        <h3 className="mb-3 text-base font-semibold text-ink-100">
          Dataset status JSON
        </h3>
        <pre className="overflow-auto rounded-xl bg-surface-950/70 p-3 font-mono text-xs text-ink-300">
          {JSON.stringify(datasets ?? {}, null, 2)}
        </pre>
      </div>
    </div>
  )
}
