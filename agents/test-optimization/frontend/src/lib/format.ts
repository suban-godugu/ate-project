import type { FlowMode, RiskLevel } from "./types";

export const pct = (value: number) => `${Math.round(value * 100)}%`;

export const num = (value: number, digits = 1) =>
  value.toLocaleString(undefined, { maximumFractionDigits: digits });

export function formatDate(iso: string) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export const riskTone: Record<RiskLevel, string> = {
  Low: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
  Medium: "border-amber-500/30 bg-amber-500/10 text-amber-300",
  High: "border-rose-500/30 bg-rose-500/10 text-rose-300",
};

export const riskHex: Record<RiskLevel, string> = {
  Low: "#34d399",
  Medium: "#fbbf24",
  High: "#fb7185",
};

export const flowTone: Record<FlowMode, string> = {
  full: "border-sky-500/30 bg-sky-500/10 text-sky-300",
  reduced: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
  extended: "border-rose-500/30 bg-rose-500/10 text-rose-300",
  skip: "border-slate-500/30 bg-slate-500/10 text-slate-300",
};

/** Renders `estimated_impact` values without inventing or rounding away detail. */
export function formatImpactValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (Array.isArray(value)) return value.map(formatImpactValue).join(", ");
  if (typeof value === "number") return num(value, 3);
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

export const titleize = (key: string) =>
  key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
