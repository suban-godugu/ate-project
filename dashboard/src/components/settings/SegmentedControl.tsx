import { cn } from "@/lib/utils";

interface SegmentedControlProps<T extends string> {
  options: { value: T; label: string }[];
  value: T;
  onChange: (value: T) => void;
  className?: string;
  accentColor?: string;
}

export function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
  className,
  accentColor = "#7C3AED",
}: SegmentedControlProps<T>) {
  return (
    <div
      className={cn(
        "inline-flex rounded-xl border border-[#2D3748] bg-[#0A1020]/80 p-1",
        className
      )}
    >
      {options.map((opt) => {
        const active = value === opt.value;
        return (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            className={cn(
              "rounded-lg px-4 py-2 text-xs font-medium transition-all duration-200",
              active
                ? "text-white shadow-md"
                : "text-slate-400 hover:text-slate-200"
            )}
            style={
              active
                ? { backgroundColor: accentColor, boxShadow: `0 4px 14px ${accentColor}40` }
                : undefined
            }
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
