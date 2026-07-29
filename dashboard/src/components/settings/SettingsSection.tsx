import { cn } from "@/lib/utils";

interface SettingsSectionProps {
  title: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
  divider?: boolean;
}

export function SettingsSection({
  title,
  description,
  children,
  className,
  divider = true,
}: SettingsSectionProps) {
  return (
    <section className={cn("space-y-4", className)}>
      <div>
        <h4 className="text-sm font-semibold text-white">{title}</h4>
        {description && (
          <p className="mt-0.5 text-xs text-slate-500">{description}</p>
        )}
      </div>
      {children}
      {divider && <div className="h-px bg-gradient-to-r from-transparent via-[#2D3748] to-transparent" />}
    </section>
  );
}

interface SettingsRowProps {
  label: string;
  children: React.ReactNode;
  className?: string;
}

export function SettingsRow({ label, children, className }: SettingsRowProps) {
  return (
    <div className={cn("flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between", className)}>
      <span className="text-sm text-slate-400">{label}</span>
      <div className="sm:text-right">{children}</div>
    </div>
  );
}
