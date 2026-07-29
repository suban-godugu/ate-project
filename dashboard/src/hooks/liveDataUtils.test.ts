import { describe, expect, it } from "vitest";
import { emptyLiveShell, hasLiveContent } from "@/hooks/liveDataUtils";
import type { DashboardTabData } from "@/lib/api/dashboard";

describe("emptyLiveShell", () => {
  it("strips array fields and replaces functions with empty-array factories", () => {
    const template = {
      kpis: [{ id: "1" }],
      rows: [{ id: "a" }],
      chartData: [1, 2, 3],
      buildHeatmap: () => [{ value: 1 }],
      title: "keep me",
    };
    const shell = emptyLiveShell(template);
    expect(shell.kpis).toEqual([]);
    expect(shell.rows).toEqual([]);
    expect(shell.chartData).toEqual([]);
    expect(typeof shell.buildHeatmap).toBe("function");
    expect(shell.buildHeatmap()).toEqual([]);
    expect(shell.title).toBe("keep me");
  });
});

describe("hasLiveContent", () => {
  it("returns false for empty API payload", () => {
    const api: DashboardTabData = { kpis: [], rows: [], charts: {} };
    expect(hasLiveContent(api)).toBe(false);
  });

  it("returns true when KPIs or rows exist", () => {
    expect(hasLiveContent({ kpis: [{ id: "k1", title: "t", value: "1", change: 0, trend: "up", sparkline: [] }] })).toBe(true);
    expect(hasLiveContent({ rows: [{ id: "1" }] })).toBe(true);
  });

  it("detects non-empty chart series", () => {
    expect(hasLiveContent({ charts: { trend: [{ label: "A", value: 1 }] } })).toBe(true);
  });
});
