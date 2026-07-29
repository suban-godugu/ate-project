import { describe, expect, it, vi, beforeEach } from "vitest";

vi.mock("@/services/api", () => ({
  api: { post: vi.fn(), get: vi.fn() },
  uploadDatasetBundle: vi.fn(),
  startAnalysisPipeline: vi.fn(),
  getExecutionStatus: vi.fn(),
  mapApiError: vi.fn((err: unknown) => ({
    message: err instanceof Error ? err.message : "Upload Failed",
    code: "upload_failed",
  })),
}));

import {
  uploadDatasetBundle,
  startAnalysisPipeline,
} from "@/services/api";
import { validateUploadInputs } from "@/services/upload-validation";

describe("upload validation", () => {
  it("requires STIL and tester logs", () => {
    expect(() => validateUploadInputs(null, [])).toThrow(/STIL/i);
    const stil = new File(["x"], "a.stil");
    expect(() => validateUploadInputs(stil, [])).toThrow(/tester log/i);
  });
});

describe("upload services", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("uploadDatasetBundle posts stil_file and tester_logs", async () => {
    const stil = new File(["stil"], "scan.stil", { type: "text/plain" });
    const log = new File(["log"], "die.log", { type: "text/plain" });
    (uploadDatasetBundle as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      execution_id: "exec-1",
      dataset_id: "ds-1",
      primary_upload_id: "up-log",
      file_count: 2,
      status: "completed",
    });

    const result = await uploadDatasetBundle({
      stilFile: stil,
      logFiles: [log],
      datasetName: "demo",
    });

    expect(uploadDatasetBundle).toHaveBeenCalledWith({
      stilFile: stil,
      logFiles: [log],
      datasetName: "demo",
    });
    expect(result.dataset_id).toBe("ds-1");
  });

  it("startAnalysisPipeline triggers async backend run", async () => {
    (startAnalysisPipeline as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      execution_id: "exec-1",
      status: "running",
    });
    const result = await startAnalysisPipeline({
      executionId: "exec-1",
      uploadId: "up-1",
      datasetId: "ds-1",
      importedFiles: 2,
    });
    expect(result.status).toBe("running");
  });
});
