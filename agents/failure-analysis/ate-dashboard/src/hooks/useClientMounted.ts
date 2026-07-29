"use client";

import { useEffect, useState } from "react";

/** True after mount — use to gate UI that reads persisted client-only state (localStorage). */
export function useClientMounted() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  return mounted;
}
