"use client";

import { createContext, useContext } from "react";
import type { ScanChainTab } from "@/types/scanChain";

const ScanChainNavigationContext = createContext<(tab: ScanChainTab) => void>(() => {});

export function ScanChainNavigationProvider({
  onNavigate,
  children,
}: {
  onNavigate: (tab: ScanChainTab) => void;
  children: React.ReactNode;
}) {
  return (
    <ScanChainNavigationContext.Provider value={onNavigate}>
      {children}
    </ScanChainNavigationContext.Provider>
  );
}

export function useScanChainNavigation() {
  return useContext(ScanChainNavigationContext);
}
