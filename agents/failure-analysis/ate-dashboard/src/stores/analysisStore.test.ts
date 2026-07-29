import { describe, expect, it, beforeEach } from "vitest";
import { useAnalysisStore } from "@/stores/analysisStore";

describe("analysisStore", () => {
  beforeEach(() => {
    useAnalysisStore.getState().reset();
  });

  it("stores backend metrics and charts via applyDashboard", () => {
    useAnalysisStore.getState().applyDashboard({
      execution_id: "e1",
      dataset_id: "d1",
      upload_id: "u1",
      status: "completed",
      metrics: {
        imported_test_files: 3,
        overall_failure_rate: 12.5,
        ai_detection_accuracy: 97,
        failing_test_patterns: 8,
        die_failure_rate: 10,
        wafer_failure_rate: 11,
        lot_failure_rate: 9,
        fault_categories: 4,
        root_cause_confidence: 80,
        recurring_failures: 2,
        failure_correlations: 5,
        failure_reports: 1,
        processing_time: 4200,
        total_tests: 100,
        total_failed: 12,
        total_passed: 88,
      },
      charts: {
        failure_trend: [{ label: "lot_a", rate: 5 }],
        failure_distribution: [],
        category_distribution: [],
        pass_vs_fail: [],
        wafer_heatmap: [],
        die_heatmap: [],
        correlation_graph: {},
      },
    });
    expect(useAnalysisStore.getState().metrics?.imported_test_files).toBe(3);
    expect(useAnalysisStore.getState().charts?.failure_trend).toHaveLength(1);
    expect(useAnalysisStore.getState().executionId).toBe("e1");
  });
});
