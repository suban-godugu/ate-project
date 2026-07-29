import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPercent(value: number | null | undefined, digits = 2): string {
  if (value == null || Number.isNaN(Number(value))) return "—";
  return `${Number(value).toFixed(digits)}%`;
}

export function formatNumber(value: number | null | undefined): string {
  if (value == null || Number.isNaN(Number(value))) return "—";
  return String(value);
}

export function toDataUrl(raw?: string | null): string | null {
  if (!raw) return null;
  if (raw.startsWith("data:")) return raw;
  return `data:image/png;base64,${raw}`;
}

export function displayWaferName(result: {
  source_file?: string;
  wafer_id?: string;
}): string {
  return result.source_file || result.wafer_id || "Wafer";
}
