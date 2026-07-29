/** Static display taxonomy — mirrors backend DEFECT_CLASSES order (LOT_1…LOT_9). */
export const DEFECT_CLASSES = [
  "Center",
  "Donut",
  "Edge-Loc",
  "Edge-Ring",
  "Local",
  "Near-Full",
  "Normal",
  "Random",
  "Scratch",
] as const;

export type DefectClass = (typeof DEFECT_CLASSES)[number];

export const LOT_TAXONOMY: ReadonlyArray<{ lot: string; defect: DefectClass }> = [
  { lot: "LOT_1", defect: "Center" },
  { lot: "LOT_2", defect: "Donut" },
  { lot: "LOT_3", defect: "Edge-Loc" },
  { lot: "LOT_4", defect: "Edge-Ring" },
  { lot: "LOT_5", defect: "Local" },
  { lot: "LOT_6", defect: "Near-Full" },
  { lot: "LOT_7", defect: "Normal" },
  { lot: "LOT_8", defect: "Random" },
  { lot: "LOT_9", defect: "Scratch" },
];

const DEFECT_TO_LOT: Record<string, string> = Object.fromEntries(
  LOT_TAXONOMY.map(({ lot, defect }) => [defect.toLowerCase(), lot]),
);

const LOT_TO_DEFECT: Record<string, string> = Object.fromEntries(
  LOT_TAXONOMY.map(({ lot, defect }) => [lot.toUpperCase(), defect]),
);

/** Map defect_type → LOT_n for UI when API omits assigned_lot. */
export function lotCodeFromDefect(defectType: string | null | undefined): string | null {
  if (!defectType) return null;
  return DEFECT_TO_LOT[defectType.trim().toLowerCase()] ?? null;
}

export function defectFromLotCode(lot: string | null | undefined): string | null {
  if (!lot) return null;
  return LOT_TO_DEFECT[lot.trim().toUpperCase()] ?? null;
}
