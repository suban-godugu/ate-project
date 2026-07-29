import type { LucideIcon } from 'lucide-react'
import { Link } from 'react-router-dom'

interface StatCardProps {
  label: string
  value: string | number
  sublabel?: string
  icon?: LucideIcon
  to?: string
  accent?: boolean
}

export function StatCard({
  label,
  value,
  sublabel,
  icon: Icon,
  to,
  accent,
}: StatCardProps) {
  const body = (
    <div
      className={`card-surface card-hover h-full p-4 ${
        accent ? 'border-accent-600/35 bg-accent-700/10' : ''
      } ${to ? 'cursor-pointer' : ''}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-400">
            {label}
          </p>
          <p className="mt-2 font-mono text-xl font-medium text-ink-100 break-words">
            {value}
          </p>
          {sublabel ? (
            <p className="mt-1 text-xs text-ink-400">{sublabel}</p>
          ) : null}
        </div>
        {Icon ? (
          <div className="rounded-xl bg-accent-600/15 p-2 text-accent-400">
            <Icon size={18} />
          </div>
        ) : null}
      </div>
    </div>
  )

  if (to) {
    return (
      <Link to={to} className="block h-full no-underline">
        {body}
      </Link>
    )
  }
  return body
}
