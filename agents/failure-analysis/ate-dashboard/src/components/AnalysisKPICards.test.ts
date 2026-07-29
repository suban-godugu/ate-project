import { describe, expect, it } from "vitest";
import { normalizeMetrics, normalizeCharts } from "@/services/dashboard";

describe("dashboard metrics normalization", () => {
  it("maps legacy keys to canonical API contract", () => {
    const metrics = normalizeMetrics({
      imported_files: 4,
      failing_patterns: 8,
      reports_generated: 1,
      overall_failure_rate: 12.5,
    });
    expect(metrics?.imported_test_files).toBe(4);
    expect(metrics?.failing_test_patterns).toBe(8);
    expect(metrics?.failure_reports).toBe(1);
    expect(metrics?.overall_failure_rate).toBe(12.5);
  });

  it("normalizes chart payloads", () => {
    const charts = normalizeCharts({
      failure_trend: [{ label: "lot_a", rate: 5 }],
      pass_vs_fail: [{ name: "Passed", value: 90 }],
    });
    expect(charts.failure_trend).toHaveLength(1);
    expect(charts.pass_vs_fail[0].value).toBe(90);
  });
});

describe("KPI mapping", () => {
  it("covers twelve dashboard metrics keys", () => {
    const keys = [
      "imported_test_files",
      "overall_failure_rate",
      "ai_detection_accuracy",
      "failing_test_patterns",
      "die_failure_rate",
      "wafer_failure_rate",
      "lot_failure_rate",
      "fault_categories",
      "root_cause_confidence",
      "recurring_failures",
      "failure_correlations",
      "failure_reports",
    ];
    const metrics = normalizeMetrics(
      Object.fromEntries(keys.map((k) => [k, 1])),
    );
    expect(metrics).not.toBeNull();
    for (const key of keys) {
      expect(typeof metrics![key as keyof typeof metrics]).toBe("number");
    }
  });
});
