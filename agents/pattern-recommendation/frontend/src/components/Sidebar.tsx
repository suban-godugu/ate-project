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
  return (
    <>
      <div
        className={`fixed inset-0 z-30 bg-black/50 lg:hidden ${open ? 'block' : 'hidden'}`}
        onClick={onClose}
      />
      <aside
        className={`fixed top-0 left-0 z-40 flex h-full w-64 flex-col border-r border-white/8 bg-surface-900/95 backdrop-blur-md transition-transform lg:static lg:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center gap-3 border-b border-white/8 px-5 py-5">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-600/20 text-accent-400">
            <CircuitBoard size={20} />
          </div>
          <div>
            <p className="text-sm font-semibold text-ink-100">Pattern Rec</p>
            <p className="text-xs text-ink-400">Enterprise console</p>
          </div>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition ${
                  isActive
                    ? 'bg-accent-600/20 text-accent-400'
                    : 'text-ink-300 hover:bg-white/5 hover:text-ink-100'
                }`
              }
            >
              <Icon size={17} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-white/8 px-4 py-4">
          <div className="flex items-center gap-2 rounded-xl bg-surface-850 px-3 py-2 text-xs text-ink-400">
            <Activity size={14} className="text-accent-400" />
            FastAPI · live
          </div>
        </div>
      </aside>
    </>
  )
}
