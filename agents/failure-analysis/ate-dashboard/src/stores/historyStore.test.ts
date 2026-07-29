import { describe, expect, it } from "vitest";
import { useHistoryStore } from "@/stores/historyStore";

describe("historyStore", () => {
  it("upserts entries by execution id", () => {
    useHistoryStore.setState({ entries: [], selectedExecutionId: null });
    useHistoryStore.getState().upsertEntry({
      execution_id: "exec-1",
      status: "completed",
      user: "test",
    });
    useHistoryStore.getState().upsertEntry({
      execution_id: "exec-2",
      status: "running",
      user: "test",
    });
    expect(useHistoryStore.getState().entries).toHaveLength(2);
    useHistoryStore.getState().upsertEntry({
      execution_id: "exec-1",
      status: "completed_with_failures",
      user: "test",
    });
    expect(useHistoryStore.getState().entries).toHaveLength(2);
    expect(useHistoryStore.getState().entries[0].status).toBe("completed_with_failures");
  });
});
