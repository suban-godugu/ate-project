export function LoadingSpinner({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="flex min-h-[40vh] flex-col items-center justify-center gap-3 text-ink-300">
      <div className="h-10 w-10 animate-spin rounded-full border-2 border-accent-500/30 border-t-accent-500" />
      <p className="text-sm">{label}</p>
    </div>
  )
}
