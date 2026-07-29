"use client";

import { createContext, useContext } from "react";
import type { WaferTab } from "@/types/wafer";

const WaferNavigationContext = createContext<(tab: WaferTab) => void>(() => {});

export function WaferNavigationProvider({
  onNavigate,
  children,
}: {
  onNavigate: (tab: WaferTab) => void;
  children: React.ReactNode;
}) {
  return (
    <WaferNavigationContext.Provider value={onNavigate}>
      {children}
    </WaferNavigationContext.Provider>
  );
}

export function useWaferNavigation() {
  return useContext(WaferNavigationContext);
}
