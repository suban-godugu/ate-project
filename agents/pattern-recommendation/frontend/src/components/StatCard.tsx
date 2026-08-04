import type { LucideIcon } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useEmbedMode, withEmbedParam } from '@/hooks/useEmbedMode'

interface StatCardProps {
  label: string
  value: string | number
  sublabel?: string
  icon?: LucideIcon
  to?: string
  accent?: boolean
  compact?: boolean
}

export function StatCard({
  label,
  value,
  sublabel,
  icon: Icon,
  to,
  accent,
  compact = false,
}: StatCardProps) {
  const embed = useEmbedMode()
  const body = (
    <div
      className={`card-surface card-hover h-full min-w-0 ${
        compact ? 'rounded-xl p-2.5' : 'p-4'
      } ${accent ? 'border-accent-600/35 bg-accent-700/10' : ''} ${
        to ? 'cursor-pointer' : ''
      }`}
    >
      <div className={`flex items-start justify-between ${compact ? 'gap-2' : 'gap-3'}`}>
        <div className="min-w-0">
          <p
            className={`font-semibold uppercase tracking-[0.08em] text-ink-400 ${
              compact ? 'text-[10px] leading-tight' : 'text-[11px]'
            }`}
          >
            {label}
          </p>
          <p
            className={`font-mono font-medium text-ink-100 break-words ${
              compact ? 'mt-1 text-base leading-snug' : 'mt-2 text-xl'
            }`}
          >
            {value}
          </p>
          {sublabel ? (
            <p
              className={`text-ink-400 truncate ${
                compact ? 'mt-0.5 text-[10px]' : 'mt-1 text-xs'
              }`}
            >
              {sublabel}
            </p>
          ) : null}
        </div>
        {Icon ? (
          <div
            className={`shrink-0 text-accent-400 ${
              compact
                ? 'rounded-lg bg-accent-600/15 p-1.5'
                : 'rounded-xl bg-accent-600/15 p-2'
            }`}
          >
            <Icon size={compact ? 14 : 18} />
          </div>
        ) : null}
      </div>
    </div>
  )

  if (to) {
    return (
      <Link to={withEmbedParam(to, embed)} className="block h-full min-w-0 no-underline">
        {body}
      </Link>
    )
  }
  return body
}
