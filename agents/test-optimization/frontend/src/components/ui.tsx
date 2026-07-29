import type { ReactNode } from "react";
import { AlertTriangle, Loader2 } from "lucide-react";

export function Card({
  title,
  subtitle,
  actions,
  children,
  className = "",
}: {
  title?: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`card p-4 ${className}`}>
      {(title || actions) && (
        <header className="mb-3 flex items-start justify-between gap-3">
          <div>
            {title && <h2 className="text-sm font-semibold text-ink-100">{title}</h2>}
            {subtitle && <p className="mt-0.5 text-xs text-ink-400">{subtitle}</p>}
          </div>
          {actions}
        </header>
      )}
      {children}
    </section>
  );
}

export function Badge({
  children,
  tone = "border-white/10 bg-white/5 text-ink-200",
}: {
  children: ReactNode;
  tone?: string;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-medium ${tone}`}
    >
      {children}
    </span>
  );
}

export function StatCard({
  label,
  value,
  hint,
  icon,
  tone,
}: {
  label: string;
  value: string;
  hint?: string;
  icon?: ReactNode;
  tone?: string;
}) {
  return (
    <div className="card card-hover p-4">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-medium uppercase tracking-wide text-ink-400">
          {label}
        </span>
        {icon && <span className="text-ink-400">{icon}</span>}
      </div>
      <p className={`num mt-2 text-2xl font-semibold ${tone ?? "text-ink-100"}`}>{value}</p>
      {hint && <p className="mt-1 text-xs text-ink-400">{hint}</p>}
    </div>
  );
}

export function ConfidenceBar({ value }: { value: number }) {
  const width = `${Math.round(Math.min(Math.max(value, 0), 1) * 100)}%`;
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-20 overflow-hidden rounded-full bg-white/8">
        <div className="h-full rounded-full bg-brand-500" style={{ width }} />
      </div>
      <span className="num text-xs text-ink-300">{width}</span>
    </div>
  );
}

export function Spinner({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-ink-300">
      <Loader2 className="h-6 w-6 animate-spin text-brand-400" />
      <p className="text-sm">{label}</p>
    </div>
  );
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="card flex flex-col items-center justify-center gap-3 p-10 text-center">
      <AlertTriangle className="h-6 w-6 text-amber-400" />
      <p className="text-sm font-medium text-ink-100">Could not reach the optimization API</p>
      <p className="max-w-md text-xs text-ink-400">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-1 rounded-md border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-ink-100 transition hover:border-brand-500/40"
        >
          Retry
        </button>
      )}
    </div>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-center py-12">
      <p className="text-sm text-ink-400">{message}</p>
    </div>
  );
}
