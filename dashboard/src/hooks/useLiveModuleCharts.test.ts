import { describe, expect, it } from "vitest";
import type { UseQueryResult } from "@tanstack/react-query";
import type { DashboardTabData } from "@/lib/api/dashboard";
import { buildLiveModuleResult } from "@/hooks/useLiveModuleCharts";

function mockQuery(partial: Partial<UseQueryResult<DashboardTabData>>): UseQueryResult<DashboardTabData> {
  return partial as UseQueryResult<DashboardTabData>;
}

describe("buildLiveModuleResult", () => {
  const template = {
    kpis: [{ id: "mock" }],
    rows: [{ id: "mock-row" }],
    trend: [{ label: "A", value: 1 }],
  };

  it("returns mock data unchanged in mock mode", () => {
    const result = buildLiveModuleResult(
      template,
      mockQuery({ isLoading: false, isPending: false, isError: false, isFetching: false }),
      false,
      ["trend"],
      (base) => base
    );
    expect(result.kpis).toHaveLength(1);
    expect(result.isLoading).toBe(false);
    expect(result.isEmpty).toBe(false);
  });

  it("returns empty shell while loading in live mode", () => {
    const result = buildLiveModuleResult(
      template,
      mockQuery({ isLoading: true, isPending: true, isError: false, isFetching: true }),
      true,
      ["trend"],
      (base) => base
    );
    expect(result.kpis).toEqual([]);
    expect(result.rows).toEqual([]);
    expect(result.isLoading).toBe(true);
  });

  it("never falls back to mock arrays after live fetch", () => {
    const api: DashboardTabData = { kpis: [], rows: [], charts: { trend: [] } };
    const result = buildLiveModuleResult(
      template,
      mockQuery({
        isLoading: false,
        isPending: false,
        isError: false,
        isFetching: false,
        data: api,
      }),
      true,
      ["trend"],
      (base, liveApi) => ({ ...base, rows: liveApi.rows ?? [] })
    );
    expect(result.kpis).toEqual([]);
    expect(result.rows).toEqual([]);
    expect(result.isEmpty).toBe(true);
  });

  it("merges live rows when API returns data", () => {
    const api: DashboardTabData = {
      rows: [{ id: "live-1" }],
      charts: { trend: [{ label: "B", value: 2 }] },
    };
    const result = buildLiveModuleResult(
      template,
      mockQuery({
        isLoading: false,
        isPending: false,
        isError: false,
        isFetching: false,
        data: api,
      }),
      true,
      ["trend"],
      (base, liveApi) => ({ ...base, rows: liveApi.rows ?? [] })
    );
    expect(result.rows).toEqual([{ id: "live-1" }]);
    expect(result.isEmpty).toBe(false);
  });
});
