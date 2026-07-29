export const LOT_TAXONOMY = [
  { lot: "LOT_1", defect: "Center" },
  { lot: "LOT_2", defect: "Donut" },
  { lot: "LOT_3", defect: "Edge-Loc" },
  { lot: "LOT_4", defect: "Edge-Ring" },
  { lot: "LOT_5", defect: "Local" },
  { lot: "LOT_6", defect: "Near-Full" },
  { lot: "LOT_7", defect: "Normal" },
  { lot: "LOT_8", defect: "Random" },
  { lot: "LOT_9", defect: "Scratch" },
] as const;

export type LotCode = (typeof LOT_TAXONOMY)[number]["lot"];

export function defectToLot(defect?: string | null): string | null {
  if (!defect) return null;
  const found = LOT_TAXONOMY.find(
    (item) => item.defect.toLowerCase() === defect.toLowerCase()
  );
  return found?.lot ?? null;
}

export function lotToDefect(lot?: string | null): string | null {
  if (!lot) return null;
  const found = LOT_TAXONOMY.find(
    (item) => item.lot.toUpperCase() === lot.toUpperCase()
  );
  return found?.defect ?? null;
}

export function lotLabel(lot: string): string {
  const defect = lotToDefect(lot);
  return defect ? `${lot} (${defect})` : lot;
}
