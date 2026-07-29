import type { ReactNode } from 'react'

interface BadgeProps {
  children: ReactNode
  tone?: 'neutral' | 'success' | 'warning' | 'danger' | 'accent'
}

const tones: Record<NonNullable<BadgeProps['tone']>, string> = {
  neutral: 'bg-white/8 text-ink-200 border-white/10',
  success: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/25',
  warning: 'bg-amber-500/15 text-amber-300 border-amber-500/25',
  danger: 'bg-rose-500/15 text-rose-300 border-rose-500/25',
  accent: 'bg-accent-600/20 text-accent-400 border-accent-500/30',
}

export function Badge({ children, tone = 'neutral' }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${tones[tone]}`}
    >
      {children}
    </span>
  )
}

export function severityTone(severity: string): BadgeProps['tone'] {
  const s = severity.toUpperCase()
  if (s === 'HIGH') return 'danger'
  if (s === 'MEDIUM') return 'warning'
  if (s === 'LOW') return 'success'
  return 'neutral'
}
