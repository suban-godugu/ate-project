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

  const embedMode = new URLSearchParams(location.search).get('embed') === '1'

  // Same chrome as standalone (sidebar + top bar) — embed only densifies spacing.
  return (
    <div
      className={`flex overflow-x-hidden bg-[#090b12] ${
        embedMode ? 'h-full min-h-0' : 'min-h-screen'
      }`}
    >
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
        <main
          className={`min-w-0 flex-1 overflow-x-hidden overflow-y-auto ${
            embedMode ? 'px-2 py-2 lg:px-3' : 'px-3 py-4 lg:px-5'
          }`}
        >
          {errors.length > 0 ? (
            <div
              className={`mb-2 rounded-xl border border-amber-500/25 bg-amber-500/10 ${
                embedMode ? 'px-2.5 py-1.5' : 'px-3 py-2'
              }`}
            >
              <p
                className={`text-amber-200 ${embedMode ? 'truncate text-[11px]' : 'text-xs'}`}
                title={errors.join(' · ')}
              >
                {errors.length === 1
                  ? errors[0]
                  : `${errors.length} data sources unavailable — ${errors[0]}`}
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
