import type { ReactNode } from 'react'

interface FiltersProps {
  children: ReactNode
}

/** Shared filter toolbar shell for table pages. */
export function Filters({ children }: FiltersProps) {
  return (
    <div className="card-surface grid gap-3 p-4 md:grid-cols-2 xl:grid-cols-4">
      {children}
    </div>
  )
}
