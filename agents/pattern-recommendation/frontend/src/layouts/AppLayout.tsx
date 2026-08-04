import { useEffect, useMemo, useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from '@/components/Sidebar'
import { TopNavbar } from '@/components/TopNavbar'
import { Toast } from '@/components/Toast'
import { UploadDialog } from '@/components/UploadDialog'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { useDashboardStore } from '@/contexts/dashboardStore'

const TITLES: Record<string, { title: string; subtitle: string }> = {
  '/': {
    title: 'Pattern Recommendation',
    subtitle: 'Failure aggregation and pattern analytics console',
  },
  '/failures': {
    title: 'Failure Aggregation',
    subtitle: 'Log → aggregate pipeline across ATE lots',
  },
  '/removal': {
    title: 'Pattern Removal',
    subtitle: 'Ranked removal candidates for redundant near-duplicates',
  },
  '/ordering': {
    title: 'Pattern Ordering',
    subtitle: 'Early failure detection execution order',
  },
  '/redundancy': {
    title: 'Redundant Pattern Detection',
    subtitle: 'Clustering-based near-duplicate patterns',
  },
  '/gap': {
    title: 'Gap Analysis',
    subtitle: 'ATPG requests only — no vectors generated',
  },
  '/low-power': {
    title: 'Low-Power Proxy',
    subtitle: 'Toggle-activity proxy — not measured power',
  },
  '/coverage': {
    title: 'Coverage Proxy',
    subtitle: 'Toggle/fail proxy — not ATPG fault coverage',
  },
  '/settings': {
    title: 'Settings',
    subtitle: 'API health, datasets, and refresh controls',
  },
}

export function AppLayout() {
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [uploadOpen, setUploadOpen] = useState(false)

  const loading = useDashboardStore((s) => s.loading)
  const refreshing = useDashboardStore((s) => s.refreshing)
  const healthOk = useDashboardStore((s) => s.healthOk)
  const globalSearch = useDashboardStore((s) => s.globalSearch)
  const errors = useDashboardStore((s) => s.errors)
  const loadAll = useDashboardStore((s) => s.loadAll)
  const refreshAll = useDashboardStore((s) => s.refreshAll)
  const setGlobalSearch = useDashboardStore((s) => s.setGlobalSearch)

  useEffect(() => {
    void loadAll().catch(() => undefined)
  }, [loadAll])

  const meta = useMemo(
    () => TITLES[location.pathname] ?? TITLES['/'],
    [location.pathname],
  )

  const embedMode = new URLSearchParams(location.search).get("embed") === "1"

  if (embedMode) {
    return (
      <div className="h-full min-h-0 overflow-x-hidden bg-[#090b12]">
        <main className="min-w-0">
          {errors.length > 0 ? (
            <div className="border-b border-amber-500/20 bg-amber-500/10 px-3 py-1.5">
              <p className="truncate text-[11px] text-amber-200" title={errors.join(' · ')}>
                {errors.length === 1
                  ? errors[0]
                  : `${errors.length} data sources unavailable — ${errors[0]}`}
              </p>
            </div>
          ) : null}
          {loading ? <LoadingSpinner label="Loading dashboard data…" /> : <Outlet />}
        </main>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen overflow-x-hidden">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopNavbar
          title={meta.title}
          subtitle={meta.subtitle}
          search={globalSearch}
          onSearchChange={setGlobalSearch}
          onMenuClick={() => setSidebarOpen(true)}
          onUploadClick={() => setUploadOpen(true)}
          onRefreshClick={() => void refreshAll()}
          refreshing={refreshing}
          healthOk={healthOk}
        />
        <main className="min-w-0 flex-1 overflow-x-hidden px-3 py-4 lg:px-5">
          {errors.length > 0 ? (
            <div className="mb-3 rounded-xl border border-amber-500/25 bg-amber-500/10 px-3 py-2">
              <p className="text-xs text-amber-200" title={errors.join(' · ')}>
                {errors.length === 1
                  ? errors[0]
                  : `${errors.length} data sources unavailable — open Settings for details.`}
              </p>
            </div>
          ) : null}
          {loading ? <LoadingSpinner label="Loading dashboard data…" /> : <Outlet />}
        </main>
      </div>
      <Toast />
      <UploadDialog
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        refreshing={refreshing}
        onRefresh={() => {
          void refreshAll().then(() => setUploadOpen(false))
        }}
      />
    </div>
  )
}
