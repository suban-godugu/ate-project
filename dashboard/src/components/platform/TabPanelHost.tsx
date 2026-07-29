"use client";

import { useEffect, useState, type ComponentType } from "react";
import { cn } from "@/lib/utils";

interface TabPanelHostProps<T extends string> {
  activeTab: T;
  tabs: Record<T, ComponentType>;
  className?: string;
}

export function TabPanelHost<T extends string>({
  activeTab,
  tabs,
  className = "mt-6",
}: TabPanelHostProps<T>) {
  const [mountedTabs, setMountedTabs] = useState<Set<T>>(() => new Set([activeTab]));

  useEffect(() => {
    setMountedTabs((prev) => {
      if (prev.has(activeTab)) return prev;
      const next = new Set(prev);
      next.add(activeTab);
      return next;
    });
  }, [activeTab]);

  return (
    <>
      {(Object.entries(tabs) as [T, ComponentType][]).map(([tabId, TabComponent]) => {
        if (!mountedTabs.has(tabId)) return null;
        return (
          <div
            key={tabId}
            className={cn(className, activeTab !== tabId && "hidden")}
            aria-hidden={activeTab !== tabId}
          >
            <TabComponent />
          </div>
        );
      })}
    </>
  );
}
