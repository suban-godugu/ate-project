"use client";

import { useEffect } from "react";

/** Auto-pick the first available id so Analyze / Detect is ready after platform ingest. */
export function useAutoSelectFirstId(
  current: string,
  setCurrent: (id: string) => void,
  candidates: Array<string | undefined | null> | undefined,
) {
  useEffect(() => {
    if (current) return;
    const first = (candidates || []).find((id) => Boolean(id));
    if (first) setCurrent(String(first));
  }, [current, setCurrent, candidates]);
}
