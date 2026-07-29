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
      <div className="min-h-screen bg-[#090b12]">
        <main className="flex-1 px-0 py-0">
          {errors.length > 0 ? (
            <div className="mb-4 space-y-2 px-4">
              {errors.map((err) => (
                <div
                  key={err}
                  className="rounded-xl border border-amber-500/25 bg-amber-500/10 px-4 py-2 text-sm text-amber-200"
                >
                  {err}
                </div>
              ))}
            </div>
          ) : null}
          {loading ? <LoadingSpinner label="Loading dashboard data…" /> : <Outlet />}
        </main>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen">
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
        <main className="flex-1 px-4 py-5 lg:px-6">
          {errors.length > 0 ? (
            <div className="mb-4 space-y-2">
              {errors.map((err) => (
                <div
                  key={err}
                  className="rounded-xl border border-amber-500/25 bg-amber-500/10 px-4 py-2 text-sm text-amber-200"
                >
                  {err}
                </div>
              ))}
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
