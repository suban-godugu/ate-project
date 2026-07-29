import { useDashboardStore } from '@/contexts/dashboardStore'
import { CheckCircle2, Info, X, XCircle } from 'lucide-react'

export function Toast() {
  const toasts = useDashboardStore((s) => s.toasts)
  const dismissToast = useDashboardStore((s) => s.dismissToast)

  if (!toasts.length) return null

  return (
    <div className="fixed right-4 bottom-4 z-[60] flex w-full max-w-sm flex-col gap-2">
      {toasts.map((toast) => {
        const Icon =
          toast.type === 'success'
            ? CheckCircle2
            : toast.type === 'error'
              ? XCircle
              : Info
        const color =
          toast.type === 'success'
            ? 'border-emerald-500/30 text-emerald-300'
            : toast.type === 'error'
              ? 'border-rose-500/30 text-rose-300'
              : 'border-accent-500/30 text-accent-300'
        return (
          <div
            key={toast.id}
            className={`flex items-start gap-3 rounded-xl border bg-surface-850/95 p-3 shadow-lg backdrop-blur ${color}`}
          >
            <Icon size={18} className="mt-0.5 shrink-0" />
            <p className="flex-1 text-sm text-ink-100">{toast.message}</p>
            <button
              type="button"
              onClick={() => dismissToast(toast.id)}
              className="rounded-md p-1 text-ink-400 hover:bg-white/5"
            >
              <X size={14} />
            </button>
          </div>
        )
      })}
    </div>
  )
}
