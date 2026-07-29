"use client";

import { createContext, useContext } from "react";

const ModuleTabContext = createContext<string>("overview");

export function ModuleTabProvider({
  tab,
  children,
}: {
  tab: string;
  children: React.ReactNode;
}) {
  return <ModuleTabContext.Provider value={tab}>{children}</ModuleTabContext.Provider>;
}

export function useModuleTab(fallback = "overview"): string {
  return useContext(ModuleTabContext) || fallback;
}
