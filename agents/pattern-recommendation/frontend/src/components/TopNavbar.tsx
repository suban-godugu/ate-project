import { Menu, RefreshCw, Upload, UserRound } from 'lucide-react'
import { SearchBar } from './SearchBar'
import { Badge } from './Badge'

interface TopNavbarProps {
  title: string
  subtitle?: string
  search: string
  onSearchChange: (value: string) => void
  onMenuClick: () => void
  onUploadClick: () => void
  onRefreshClick: () => void
  refreshing: boolean
  healthOk: boolean
}

export function TopNavbar({
  title,
  subtitle,
  search,
  onSearchChange,
  onMenuClick,
  onUploadClick,
  onRefreshClick,
  refreshing,
  healthOk,
}: TopNavbarProps) {
  return (
    <header className="sticky top-0 z-20 border-b border-white/8 bg-surface-950/70 backdrop-blur-md">
      <div className="flex flex-wrap items-center gap-3 px-4 py-3 lg:px-6">
        <button
          type="button"
          onClick={onMenuClick}
          className="rounded-xl border border-white/10 p-2 text-ink-300 lg:hidden hover:bg-white/5"
        >
          <Menu size={18} />
        </button>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="truncate text-lg font-semibold text-ink-100 sm:text-xl">
              {title}
            </h1>
            <Badge tone={healthOk ? 'success' : 'danger'}>
              {healthOk ? 'API healthy' : 'API down'}
            </Badge>
          </div>
          {subtitle ? (
            <p className="mt-0.5 truncate text-xs text-ink-400 sm:text-sm">{subtitle}</p>
          ) : null}
        </div>

        <div className="order-3 w-full lg:order-none lg:w-auto lg:flex-1 lg:max-w-md">
          <SearchBar value={search} onChange={onSearchChange} />
        </div>

        <div className="ml-auto flex items-center gap-2">
          <button
            type="button"
            onClick={onUploadClick}
            className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-3 py-2 text-sm text-ink-200 transition hover:border-accent-500/40 hover:text-accent-400"
          >
            <Upload size={15} />
            <span className="hidden sm:inline">Load data</span>
          </button>
          <button
            type="button"
            onClick={onRefreshClick}
            disabled={refreshing}
            className="inline-flex items-center gap-2 rounded-xl bg-accent-600 px-3 py-2 text-sm font-medium text-white transition hover:bg-accent-700 disabled:opacity-60"
          >
            <RefreshCw size={15} className={refreshing ? 'animate-spin' : ''} />
            <span className="hidden sm:inline">
              {refreshing ? 'Refreshing…' : 'Refresh All'}
            </span>
          </button>
          <div className="hidden items-center gap-2 rounded-xl border border-white/10 px-2.5 py-1.5 sm:flex">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent-600/20 text-accent-400">
              <UserRound size={16} />
            </div>
            <div className="pr-1">
              <p className="text-xs font-medium text-ink-100">Operator</p>
              <p className="text-[10px] text-ink-400">Local session</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
