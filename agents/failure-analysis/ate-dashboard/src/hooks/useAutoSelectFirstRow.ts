"use client";

import { useEffect } from "react";

/**
 * Auto-pick the first row so selection-gated evidence panels (timelines, radial
 * profiles, engineering recommendations) render immediately instead of showing a
 * "select a row" placeholder on first load.
 */
export function useAutoSelectFirstRow<T>(
  current: T | null | undefined,
  setCurrent: (row: T) => void,
  rows: readonly T[] | undefined,
) {
  const first = rows && rows.length ? rows[0] : undefined;
  useEffect(() => {
    if (current || !first) return;
    setCurrent(first);
  }, [current, first, setCurrent]);
}
