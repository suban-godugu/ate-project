import { Search } from 'lucide-react'

interface SearchBarProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
}

export function SearchBar({
  value,
  onChange,
  placeholder = 'Search patterns…',
}: SearchBarProps) {
  return (
    <div className="relative w-full max-w-md">
      <Search
        size={16}
        className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-ink-400"
      />
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-xl border border-white/10 bg-surface-900/70 py-2.5 pr-3 pl-9 text-sm text-ink-100 outline-none transition placeholder:text-ink-400 focus:border-accent-500/50 focus:ring-2 focus:ring-accent-600/20"
      />
    </div>
  )
}
