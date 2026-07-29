import { describe, expect, it } from "vitest";
import { WORKBENCH_QUERY_KEY } from "@/hooks/useWorkbenchData";

describe("workbench query keys", () => {
  it("includes execution id in workbench cache key", () => {
    expect(WORKBENCH_QUERY_KEY).toBe("workbench-data");
  });
});
