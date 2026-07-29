import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

import type { WaferAnalysisResult } from "@/types/wafer";
import { lotCodeFromDefect } from "@/utils/lotTaxonomy";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/** Display helper — reads LOT from backend fields only (never invents new engineering logic). */
export function readAssignedLot(result: WaferAnalysisResult | null): string {
  if (!result) return "—";
  const fromRoot =
    (typeof result.assigned_lot === "string" && result.assigned_lot) ||
    (typeof result.lot === "string" && result.lot) ||
    null;
  const fromClass =
    (typeof result.classification?.assigned_lot === "string" &&
      result.classification.assigned_lot) ||
    (typeof result.classification?.lot === "string" &&
      result.classification.lot) ||
    null;
  return fromRoot || fromClass || "—";
}

/** LOT for UI: API value if present, else static taxonomy from defect_type. */
export function displayLot(result: WaferAnalysisResult | null): string {
  if (!result) return "—";
  const api = readAssignedLot(result);
  if (api !== "—") return api;
  return lotCodeFromDefect(readDefectType(result)) || "—";
}

export function readDefectType(result: WaferAnalysisResult | null): string {
  if (!result) return "—";
  return result.classification?.defect_type || "—";
}

export function readWaferName(result: WaferAnalysisResult | null): string {
  if (!result) return "—";
  if (typeof result.source_file === "string" && result.source_file) {
    return result.source_file;
  }
  return result.wafer_id || "—";
}

export function toDataUrl(base64?: string): string | null {
  if (!base64) return null;
  if (base64.startsWith("data:")) return base64;
  return `data:image/png;base64,${base64}`;
}

export function formatPercent(value: number | undefined | null): string {
  if (value == null || Number.isNaN(Number(value))) return "—";
  return `${Number(value).toFixed(2)}%`;
}

export const ACCEPTED_IMAGE_TYPES = [
  "image/jpeg",
  "image/jpg",
  "image/png",
  "image/bmp",
  "image/x-ms-bmp",
];

export const ACCEPTED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp"];
