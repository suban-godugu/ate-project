import type { ReactNode } from 'react'
import { Badge } from './Badge'

interface RecommendationCardProps {
  title: string
  description?: string
  badge?: string
  children?: ReactNode
  action?: ReactNode
}

export function RecommendationCard({
  title,
  description,
  badge,
  children,
  action,
}: RecommendationCardProps) {
  return (
    <div className="card-surface card-hover p-4">
      <div className="mb-2 flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-ink-100">{title}</h3>
          {description ? (
            <p className="mt-1 text-xs text-ink-400">{description}</p>
          ) : null}
        </div>
        {badge ? <Badge tone="accent">{badge}</Badge> : null}
      </div>
      {children}
      {action ? <div className="mt-3">{action}</div> : null}
    </div>
  )
}
