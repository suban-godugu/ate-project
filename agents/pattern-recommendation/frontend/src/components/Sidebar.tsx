import { NavLink } from 'react-router-dom'
import {
  Activity,
  ArrowDownUp,
  CircuitBoard,
  Copy,
  Gauge,
  Layers3,
  LayoutDashboard,
  Settings,
  ShieldAlert,
  Trash2,
  Zap,
} from 'lucide-react'
import { useEmbedMode, withEmbedParam } from '@/hooks/useEmbedMode'

const navItems = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/failures', label: 'Failure Aggregation', icon: ShieldAlert },
  { to: '/removal', label: 'Pattern Removal', icon: Trash2 },
  { to: '/ordering', label: 'Pattern Ordering', icon: ArrowDownUp },
  { to: '/redundancy', label: 'Redundancy', icon: Copy },
  { to: '/gap', label: 'Gap Analysis', icon: Layers3 },
  { to: '/low-power', label: 'Low-Power', icon: Zap },
  { to: '/coverage', label: 'Coverage', icon: Gauge },
  { to: '/settings', label: 'Settings', icon: Settings },
]

interface SidebarProps {
  open: boolean
  onClose: () => void
}

export function Sidebar({ open, onClose }: SidebarProps) {
  const embed = useEmbedMode()
  // Embed iframe is often < lg width — keep sidebar always visible like standalone.
  const alwaysShow = embed

  return (
    <>
      {!alwaysShow ? (
        <div
          className={`fixed inset-0 z-30 bg-black/50 lg:hidden ${open ? 'block' : 'hidden'}`}
          onClick={onClose}
        />
      ) : null}
      <aside
        className={`z-40 flex shrink-0 flex-col border-r border-white/8 bg-surface-900/95 backdrop-blur-md transition-transform ${
          alwaysShow ? 'h-full w-52' : 'h-full w-56'
        } ${
          alwaysShow
            ? 'static translate-x-0'
            : `fixed top-0 left-0 lg:static lg:translate-x-0 ${
                open ? 'translate-x-0' : '-translate-x-full'
              }`
        }`}
      >
        <div className="flex items-center gap-2.5 border-b border-white/8 px-3 py-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-600/20 text-accent-400">
            <CircuitBoard size={16} />
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-ink-100">Pattern Rec</p>
            <p className="truncate text-[11px] text-ink-400">Enterprise console</p>
          </div>
        </div>

        <nav className="flex-1 space-y-0.5 overflow-y-auto px-2 py-2.5">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={withEmbedParam(to, embed)}
              end={to === '/'}
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-2 rounded-lg px-2 py-1.5 text-[12px] transition ${
                  isActive
                    ? 'bg-accent-600/20 text-accent-400'
                    : 'text-ink-300 hover:bg-white/5 hover:text-ink-100'
                }`
              }
            >
              <Icon size={15} className="shrink-0" />
              <span className="truncate">{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-white/8 px-2.5 py-2.5">
          <div className="flex items-center gap-2 rounded-lg bg-surface-850 px-2 py-1.5 text-[11px] text-ink-400">
            <Activity size={12} className="text-accent-400" />
            FastAPI · live
          </div>
        </div>
      </aside>
    </>
  )
}
