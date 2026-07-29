import { describe, expect, it, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { ModuleTabProvider } from "@/contexts/ModuleTabContext";
import { useModuleDashboard } from "@/hooks/useModuleDashboard";
import type { DashboardTabData } from "@/lib/api/dashboard";

vi.mock("@/lib/api/config", () => ({
  isLiveApi: () => true,
}));

vi.mock("@/stores/filterStore", () => ({
  useFilterStore: (selector: (s: { filters: Record<string, unknown> }) => unknown) =>
    selector({ filters: { fab: "fab-12" } }),
}));

const fetchTab = vi.fn(async (tab: string): Promise<DashboardTabData> => ({
  rows: [{ id: `${tab}-row` }],
}));

function wrapper(tab: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={client}>
      <ModuleTabProvider tab={tab}>{children}</ModuleTabProvider>
    </QueryClientProvider>
  );
}

describe("useModuleDashboard", () => {
  it("builds query key from module, tab, and filters", async () => {
    const mockBuilder = () => ({ rows: [{ id: "mock" }], trend: [] as { label: string; value: number }[] });
    const applyLive = (base: typeof mockBuilder extends () => infer R ? R : never, api: DashboardTabData) => ({
      ...base,
      rows: api.rows ?? [],
    });

    const { result } = renderHook(
      () => useModuleDashboard("scan-chain", mockBuilder, ["trend"], applyLive, fetchTab),
      { wrapper: wrapper("overview") }
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(fetchTab).toHaveBeenCalledWith("overview", { fab: "fab-12" });
    expect(result.current.rows).toEqual([{ id: "overview-row" }]);
  });

  it("uses active tab from ModuleTabProvider in fetchTab", async () => {
    fetchTab.mockClear();
    const mockBuilder = () => ({ rows: [] as { id: string }[], trend: [] as { label: string; value: number }[] });
    const applyLive = (base: ReturnType<typeof mockBuilder>, api: DashboardTabData) => ({
      ...base,
      rows: api.rows ?? [],
    });

    const { result } = renderHook(
      () => useModuleDashboard("scan-chain", mockBuilder, ["trend"], applyLive, fetchTab),
      { wrapper: wrapper("pattern-agent") }
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(fetchTab).toHaveBeenCalledWith("pattern-agent", { fab: "fab-12" });
  });
});
